from datetime import datetime as dt

from airflow import DAG
from airflow.operators.python import PythonVirtualenvOperator


def fires_pipeline():
    from datetime import datetime as dt

    from arcgis.features import FeatureLayer

    from config import URL_FIRES
    from conn import PgConn

    def transform_features(data):
        df = []
        for i in data:
            i.attributes['DetectDate'] = str(dt.strptime(i.attributes['DetectDate'], "%d.%m.%Y %H:%M"))
            i.attributes['LastDate'] = str(dt.strptime(i.attributes['LastDate'], "%d.%m.%Y %H:%M"))
            i.attributes['SHAPE'] = f"SRID=4326;POINT({i.attributes['Longitude']} {i.attributes['Latitude']})"
            df.append(i.attributes)
        return df

    def write_fires(data):
        db = PgConn()
        db.insert_execute_batch('fires', 'eks', data)
        db.close()


    # Extract
    layer = FeatureLayer(URL_FIRES)
    r = layer.query()

    # Transform
    df = transform_features(r.features)

    # Load
    write_fires(df)


with DAG(
    "fire_history", 
    start_date=dt(2021, 7, 8),
    schedule_interval="@daily",
    description='Получение исторических данных о пожарах из ЕКС',
    catchup=False    
) as dag:
    task_get_fires = PythonVirtualenvOperator(
        task_id='get_fires_history',
        requirements=["arcgis==1.8.5.post3"],
        python_callable=fires_pipeline,
    )

task_get_fires
