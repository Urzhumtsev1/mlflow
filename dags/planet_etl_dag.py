import base64
import json
from datetime import datetime

from airflow import DAG
from airflow.hooks.postgres_hook import PostgresHook
from airflow.hooks.S3_hook import S3Hook
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from airflow.operators.python import (
    BranchPythonOperator, 
    PythonOperator,
    PythonVirtualenvOperator)
from airflow.providers.http.hooks.http import HttpHook

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
    s = points.replace("'", '"')
    rq = json.loads(s)

    if 'manual_trigger' in points:
        return rq['manual_trigger']

    from shapely import wkt
    from shapely.geometry import mapping

    for p in rq:
        p["geometry"] = mapping(wkt.loads(p["geometry"]))
    return rq


def _get_images_thumbs(ti):
    request_params = ti.xcom_pull(task_ids="transform_data")
    hook = HttpHook(http_conn_id="PLANET_SERVICE_CONN", method="POST")
    items = {"items": request_params}
    images = hook.run(
        endpoint="planet/api/v1/thumbnail", 
        data=json.dumps(items)
    )
    return images.json()


def _get_images_assets(ti):
    request_params = ti.xcom_pull(task_ids="transform_data")
    hook = HttpHook(http_conn_id="PLANET_SERVICE_CONN", method="POST")
    items = {"items": request_params}
    images = hook.run(
        endpoint="planet/api/v1/assets", 
        data=json.dumps(items)
    )
    return images.json()


def _if_images_exists(ti):
    thumbs = ti.xcom_pull(task_ids="get_images_thumbs")
    assets = ti.xcom_pull(task_ids="get_images_assets")
    # "message" in assets: {"message": "Download quota has been exceeded."}
    if thumbs is None or "message" in assets:
        return 'dead_end'
    else:
        return ['load_images_thumbs', 'load_images_assets']


def _load_images_thumbs(ti):
    meta_data = ti.xcom_pull(task_ids="get_images_thumbs")
    s3 = S3Hook(aws_conn_id="PLANET_S3CONN_ID")
    bucket = Variable.get("PLANET_S3_BUCKET")
    for image in meta_data:
        # key - то как файл будет называться в s3, пока рандом
        # к нему можно добавить префикс с папкой. и это храним в тоге в БД. Линки не нужны.
        image_name = image["meta"]["id"] + ".png"
        s3.load_bytes(
            bytes_data=base64.b64decode(image["image"]),
            key=image_name,
            bucket_name=bucket,
            replace=False
        )
        image["shape"] = json.dumps(image["shape"])
        image["meta"] = json.dumps(image["meta"])
        image["url"] = None
        image["preview_url"] = image_name
        del image["image"]
    return meta_data


def _load_images_assets(ti):
    """
    Сама загрузка в s3 происходит в сервисе planet/api/v1/assets, 
    так как не помещается в память.
    Таска создана для более лаконичного пайплайна. 
    По своей сути простой прокси.
    """
    assets_meta = ti.xcom_pull(task_ids="get_images_thumbs")
    return assets_meta


def _merge_meta(ti):
    thumbs_meta = ti.xcom_pull(task_ids="load_images_thumbs")
    assets_meta = ti.xcom_pull(task_ids="load_images_assets")
    for i, image in enumerate(assets_meta):
        image["preview_url"] = thumbs_meta[i]["url"]
    return assets_meta


def _write_images_meta(ti):

    rows = ti.xcom_pull(task_ids="merge_meta")

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

    task_get_images_thumbs = PythonOperator(
        task_id='get_images_thumbs',
        provide_context=True,
        python_callable=_get_images_thumbs,
    )

    task_get_images_assets = PythonOperator(
        task_id='get_images_assets',
        provide_context=True,
        python_callable=_get_images_assets,
    )

    task_load_images_thumbs = PythonOperator(
        task_id='load_images_thumbs',
        provide_context=True,
        python_callable=_load_images_thumbs,
    )

    task_load_images_assets = PythonOperator(
        task_id='load_images_assets',
        provide_context=True,
        python_callable=_load_images_assets,
    )

    task_write_images_meta = PythonOperator(
        task_id='write_images_meta',
        python_callable=_write_images_meta,
    )

    task_merge_meta = PythonOperator(
        task_id='merge_meta',
        python_callable=_merge_meta,
    )

    task_if_images_exists = BranchPythonOperator(
        task_id="if_images_exists",
        python_callable=_if_images_exists
    )

    task_dead_end = BashOperator(
        task_id="dead_end",
        bash_command="echo 'No new images. Job Done'"
    )
    
task_get_points >> task_transform_data >> [task_get_images_thumbs, task_get_images_assets] >> task_if_images_exists >> [task_load_images_thumbs, task_load_images_assets, task_dead_end] 
task_load_images_thumbs >> task_merge_meta >> task_write_images_meta
task_load_images_assets >> task_merge_meta >> task_write_images_meta
