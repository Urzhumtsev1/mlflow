from datetime import datetime

from airflow import DAG
from airflow.hooks.postgres_hook import PostgresHook
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.providers.http.hooks.http import HttpHook
from airflow.providers.mongo.hooks.mongo import MongoHook


WEATHER_API_KEY = Variable.get("WEATHER_API_KEY")


def _get_points(sql):
    pg_hook = PostgresHook(postgres_conn_id="AIRFLOW_CONN_POSTGRES_WEATHER")
    records = pg_hook.get_records(sql=sql)
    return records


def _get_yandex(ti):
    points = ti.xcom_pull(task_ids="task_get_points")
    data = []
    hook = HttpHook(http_conn_id="WEATHER_CONN", method="GET")
    for point in points:
        res = hook.run(
            endpoint="api/v1/yandex", 
            headers={"api_key": WEATHER_API_KEY},
            data=point
        )
        data.append(res.json())
    return data

def _write_forecast(ti):

    forecast = ti.xcom_pull(task_ids="task_get_yandex")

    db = MongoHook(conn_id="MONGO_CONN")
    print(forecast)
    db.insert_many(mongo_collection="test_collection", docs=forecast, mongo_db="test")

with DAG(
    "weather_etl", 
    start_date=datetime(2021, 9, 16),
    schedule_interval="* 3 * * *",
    description="Получение и сохранение данных о погоде",
    catchup=False    
) as dag:
    task_get_points = PythonOperator(
        task_id="task_get_points",
        provide_context=True,
        python_callable=_get_points,
        op_kwargs={
            "sql": 'SELECT lat, lon, "limit", "hours", extra FROM weather.weather_points;'
        },
    )

    task_get_yandex = PythonOperator(
        task_id='task_get_yandex',
        provide_context=True,
        python_callable=_get_yandex,
    )

    task_write_forecast = PythonOperator(
        task_id='task_write_forecast',
        python_callable=_write_forecast,
    )
    
task_get_points >> task_get_yandex >> task_write_forecast
