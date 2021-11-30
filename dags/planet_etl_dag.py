import json
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import (
    BranchPythonOperator,
    PythonOperator,
    PythonVirtualenvOperator)
from airflow.providers.http.hooks.http import HttpHook
from airflow.providers.postgres.hooks.postgres import PostgresHook

default_args = {
    "owner": "airflow",
    # 'email_on_failure': True,
    # 'email': ['maurzhumtsev@greenatom.ru', 'pvservatkin@greenatom.ru'],
}


def _get_points(**kwargs):
    """
    DAG Parameters Example. Если хотим триггернуть DAG c параметрами. 
        {"targets": {
            "manual_trigger": [
                {
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [66.71679496765137, 66.56007952524924],
                            [66.76005363464355, 66.56007952524924],
                            [66.76005363464355, 66.57584828482366],
                            [66.71679496765137, 66.57584828482366],
                            [66.71679496765137, 66.56007952524924]
                        ]]
                    },
                    "gte": "2021-09-27T14:01:52.018597",
                    "lte": "2021-11-26T14:01:52.018601",
                    "num_thumbs": 1,
                    "cloud_cover": 0.3,
                    "filter": {
                        "need_padding": true,
                        "padding_scaler": 4
                    }
                }
            ]
        }}
    """
    dag_run = kwargs.get('dag_run')
    if 'targets' in dag_run.conf:
        parameters = dag_run.conf['targets']
        parameters = json.dumps(parameters)
        return parameters
    pg_hook = PostgresHook(postgres_conn_id="AIRFLOW_CONN_PG_PLANET_ETL")
    sql = """
        SELECT
            ST_AsText(shape) as geometry,
            COALESCE(to_char((now() - INTERVAL '10 DAY')::date, 'YYYY-MM-DD"T"HH:MI:SS'), '') AS gte,
            COALESCE(to_char(now()::date, 'YYYY-MM-DD"T"HH:MI:SS'), '') AS lte,
            num_thumbs
        FROM images.scan_points
        WHERE source = 'planet';
    """
    records = pg_hook.get_records(sql=sql)
    return records


def _transform_records_to_request_params(points):
    """
    PythonVirtualenvOperator не может принимать task instance. 
    Поэтому надо передавать ti через op_kwargs.

    Args:
        points (str): [description]

    Returns:
        request_params (list[dict]): [description]
    """
    import json
    points = points.replace("'", '"')
    points = json.loads(points)
    if 'manual_trigger' in points:
        return points['manual_trigger']

    from shapely import wkt
    from shapely.geometry import mapping

    for p in points:
        p["geometry"] = mapping(wkt.loads(p["geometry"]))
    return points


def _get_images_assets(ti):
    request_params = ti.xcom_pull(task_ids="transform_data")
    hook = HttpHook(http_conn_id="PLANET_SERVICE_CONN", method="POST")
    items = {"items": request_params}
    images = hook.run(
        endpoint="planet/api/v1/clipping", 
        data=json.dumps(items)
    )
    rows = json.dumps(images.json())
    return rows


def _if_images_exists(ti):
    assets = ti.xcom_pull(task_ids="get_images_assets")
    assets = json.loads(assets)
    # "message" in assets: {"message": "Download quota has been exceeded."}
    if assets is None or "message" in assets:
        return 'dead_end'
    else:
        return 'load_images_assets'


def _load_images_assets(ti):
    """
    Сама загрузка в s3 происходит в сервисе planet/api/v1/clipping, 
    так как не помещается в память.
    Таска создана для более лаконичного пайплайна. 
    По своей сути простой прокси.
    """
    assets_meta = ti.xcom_pull(task_ids="get_images_assets")
    return assets_meta

def _prepare_meta(rows):
    import json

    from shapely.geometry import shape
    rows = json.loads(rows)
    for row in rows:
        row['meta'] = json.dumps(row['meta'])
        row['shape'] = shape(row['shape']).wkt
    return rows

def _write_images_meta(ti):

    rows = ti.xcom_pull(task_ids="prepare_meta")

    db = PostgresHook(postgres_conn_id="AIRFLOW_CONN_PG_PLANET_ETL")
    conn = db.get_conn()
    cursor = conn.cursor()
    with cursor as c:
        c.executemany(f"""
                    INSERT INTO 
                        images.satellite (
                            source, shape, height, width, url, tt, meta
                        )
                    VALUES (
                        %(source)s, %(shape)s, %(height)s, %(width)s, %(url)s, %(tt)s, %(meta)s
                    )
        """, rows)
        conn.commit()
    return "Insertion done."


with DAG(
    "planet_etl", 
    start_date=datetime(2021, 10, 11),
    schedule_interval="0 2 * * *", # Раз в сутки в 2 ночи
    default_args=default_args,
    description="Получение и сохранение снимков с Planet раз в сутки, на выделенную область",
    catchup=False    
) as dag:
    task_get_points = PythonOperator(
        task_id="get_points",
        provide_context=True,
        python_callable=_get_points,
    )

    task_transform_data = PythonVirtualenvOperator(
        task_id="transform_data",
        python_callable=_transform_records_to_request_params,
        requirements=["shapely==1.7.1"],
        op_kwargs={'points': '{{ ti.xcom_pull(task_ids="get_points") }}'},
        system_site_packages=False,
    )

    task_get_images_assets = PythonOperator(
        task_id='get_images_assets',
        provide_context=True,
        python_callable=_get_images_assets,
    )

    task_load_images_assets = PythonOperator(
        task_id='load_images_assets',
        provide_context=True,
        python_callable=_load_images_assets,
    )

    task_prepare_meta = PythonVirtualenvOperator(
        task_id='prepare_meta',
        requirements=["shapely==1.7.1"],
        python_callable=_prepare_meta,
        op_kwargs={'rows': '{{ ti.xcom_pull(task_ids="load_images_assets") }}'},
        system_site_packages=False,
    )

    task_write_images_meta = PythonOperator(
        task_id='write_images_meta',
        python_callable=_write_images_meta,
    )

    task_if_images_exists = BranchPythonOperator(
        task_id="if_images_exists",
        python_callable=_if_images_exists
    )

    task_dead_end = BashOperator(
        task_id="dead_end",
        bash_command="echo 'No images for geometry. Job Done'"
    )
    
task_get_points >> task_transform_data >> task_get_images_assets >> task_if_images_exists >> [task_load_images_assets, task_dead_end] 
task_load_images_assets >> task_prepare_meta >> task_write_images_meta
