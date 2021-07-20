from datetime import datetime

import requests
from airflow import DAG
from airflow.operators.python import PythonOperator


def get_fire():
    from config import APP_LOGIN, APP_PASS, APP_HOST
    response = requests.get(
        f'http://{APP_HOST}/api/get_fires', 
        auth=(APP_LOGIN, APP_PASS)
    )
    d = response.json()
    return d

def write_fire(ti):
    from config import APP_LOGIN, APP_PASS, APP_HOST
    d = ti.xcom_pull(task_ids='get_fire_alerts')
    response = requests.post(
        f'http://{APP_HOST}/api/write_fires',
        json=d, 
        auth=(APP_LOGIN, APP_PASS)
    )
    print(response.json())

with DAG(
    "fire_alerts", 
    start_date=datetime(2021, 6, 10),
    schedule_interval="@hourly",
    description='Получение и запись новых алертов о пожарах',
    catchup=False    
) as dag:
    task_get_fire_alerts = PythonOperator(
        task_id='get_fire_alerts',
        python_callable=get_fire,
    )

    task_write_fire_alerts = PythonOperator(
        task_id='write_fire_alerts',
        python_callable=write_fire
    )
    
task_get_fire_alerts >> task_write_fire_alerts
