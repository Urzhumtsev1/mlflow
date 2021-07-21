import datetime

from airflow import DAG
from airflow.operators.sql import BranchSQLOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator

default_args = {
    "owner": "airflow", 
    'email_on_failure': True,
    'email': ['maurzhumtsev@greenatom.ru',],
}

def get_id(task_id):
    """
    Получение последнего id из таблицы,
    чтобы не перегружать всю таблицу,
    а загружать последнюю партицию.

    Args:
        task_id (str): Id таски для выбора таблицы

    Returns:
        int: Последний id в таблице
    """
    
    return 0

with DAG(
    dag_id="fires_aggrs",
    start_date=datetime.datetime(2021, 7, 20),
    schedule_interval="15 * * * *", # запуск каждый час в 15 минут
    default_args=default_args,
    description='Установка отношения точки со стпутников к определенной области geographies.regions',
    catchup=False,
) as dag:

    create_table = PostgresOperator(
        task_id="create_table",
        postgres_conn_id="POSTGRES_FIRES",
        sql="sql/create_table_fires_aggrs.sql",
    )

    data_exists = BranchSQLOperator(
        sql="sql/data_exists.sql",
        conn_id="POSTGRES_FIRES",
        follow_task_ids_if_true=["modis_partion", "viiris_partion", "eks_partion"],
        follow_task_ids_if_false=["modis_full", "viiris_full", "eks_full"],
    )

    modis_regions_full_extract = PostgresOperator(
        task_id="modis_full",
        postgres_conn_id="POSTGRES_FIRES",
        sql="sql/modis_regions_full_extract.sql",
    )
    viiris_regions_full_extract = PostgresOperator(
        task_id="viiris_full",
        postgres_conn_id="POSTGRES_FIRES",
        sql="sql/viiris_regions_full_extract.sql",
    )
    eks_regions_full_extract = PostgresOperator(
        task_id="eks_full",
        postgres_conn_id="POSTGRES_FIRES",
        sql="sql/eks_regions_full_extract.sql",
    )


    modis_regions_partion = PostgresOperator(
        task_id="modis_partion",
        postgres_conn_id="POSTGRES_FIRES",
        sql="sql/modis_regions_partion.sql",
        params={"current_id": get_id("modis_partion")},
    )
    viiris_regions_partion = PostgresOperator(
        task_id="viiris_partion",
        postgres_conn_id="POSTGRES_FIRES",
        sql="sql/viiris_regions_partion.sql",
        params={"current_id": get_id("viiris_partion")},
    )
    eks_regions_partion = PostgresOperator(
        task_id="eks_partion",
        postgres_conn_id="POSTGRES_FIRES",
        sql="sql/eks_regions_partion.sql",
        params={"current_id": get_id("eks_partion")},
    )



create_table >> data_exists >> [
    modis_regions_full_extract, 
    viiris_regions_full_extract, 
    eks_regions_full_extract,

    modis_regions_partion,
    viiris_regions_partion,
    eks_regions_partion
]