import datetime

from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator

default_args = {
    "owner": "airflow", 
    'email_on_failure': True,
    'email': ['maurzhumtsev@greenatom.ru', 'urzhumtsev.max@gmail.com'],
}


with DAG(
    dag_id="postgres_operator_dag",
    start_date=datetime.datetime(2021, 7, 20),
    schedule_interval="@once",
    default_args=default_args,
    catchup=False,
) as dag:
    create_pet_table = PostgresOperator(
        task_id="create_table",
        postgres_conn_id="POSTGRES_FIRES",
        sql="""
            CREATE TABLE IF NOT EXISTS fires.testtab (
            t_id SERIAL PRIMARY KEY
            ;
          """,
    )