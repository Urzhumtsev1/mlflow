from datetime import datetime

from airflow import DAG
from airflow.hooks.postgres_hook import PostgresHook
from airflow.operators.python import PythonOperator
from airflow.providers.http.hooks.http import HttpHook


def _extract_points():
    hook = HttpHook(http_conn_id="ISS_CONN", method="GET")
    points = hook.run(
            endpoint="iss-now.json" 
        )
    return points.json()
    


def _parse_points(ti):
    points = ti.xcom_pull(task_ids="task_extract_points")
    points['created_at'] = points['timestamp']
    points['latitude'] = points['iss_position']['latitude']
    points['longitude'] = points['iss_position']['longitude']
    del points['timestamp']
    del points['iss_position']
    return points
    

def _load_points(ti):

    points = ti.xcom_pull(task_ids="task_parse_points")

    db = PostgresHook(postgres_conn_id="AIRFLOW_CONN_POSTGRES_ISS")
    conn = db.get_conn()
    cursor = conn.cursor()
    with cursor as c:
        c.execute(f"""
                    INSERT INTO 
                        public.iss (created_at, longitude, latitude, message)
                    VALUES
                        (to_timestamp(%(created_at)s)::timestamp, %(longitude)s, %(latitude)s, %(message)s)
                """, points)
        conn.commit()
    # db.run("""
    #             INSERT INTO 
    #                 public.iss (created_at, longitude, latitude, message)
    #             VALUES
    #                 (to_timestamp(%s)::timestamp, %s, %s, %s)
    #             RETURNING created_at
    #         """, parameters=(points['created_at'], points['longitude'], points['latitude'], points['message']))
    return {"_load_points": "Done"}

with DAG(
    "iss_etl", 
    start_date=datetime(2021, 9, 23),
    schedule_interval="10 * * * *",
    description="Получение и сохранение данных местоположения МКС",
    catchup=False    
) as dag:
    task_extract_points = PythonOperator(
        task_id="task_extract_points",
        provide_context=True,
        python_callable=_extract_points,
    )

    task_parse_points = PythonOperator(
        task_id='task_parse_points',
        provide_context=True,
        python_callable=_parse_points,
    )

    task_load_points = PythonOperator(
        task_id='task_load_points',
        python_callable=_load_points,
    )
    
task_extract_points >> task_parse_points >> task_load_points
