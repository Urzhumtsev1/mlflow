import os
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import (
    BranchPythonOperator,
    PythonVirtualenvOperator
)


def _read_file(file_name):
    file_values = {}
    with open(file_name) as input_file:
        for line in input_file.readlines():
            line = line.strip()
            if "=" in line and not line.startswith("#") and not line.startswith("\n"):
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip("\"'")
                file_values[key] = value
    try:
        os.remove(file_name)
    except:
        pass
    return file_values

def _training_model():
    import os

    import mlflow
    import mlflow.keras
    import mlflow.tensorflow
    import numpy as np
    import tensorflow as tf
    from mlflow.exceptions import MlflowException
    from tensorflow import keras

    from config import URI

    mlflow.set_tracking_uri(URI)
    EXPERIMENT = 'exp_10' # Задаем имя эксперименту

    try:
        EXPERIMENT_ID = mlflow.create_experiment(
            name=EXPERIMENT, 
            artifact_location=f's3://mlflow/artifacts/{EXPERIMENT}'
        )
        mlflow.start_run(experiment_id=EXPERIMENT_ID)
    except MlflowException as e:
        mlflow.set_experiment(EXPERIMENT)
        mlflow.start_run()

    mlflow.tensorflow.autolog()
    mlflow.keras.autolog()

    model = tf.keras.Sequential([keras.layers.Dense(units=1, input_shape=[1])])

    model.compile(optimizer='sgd', loss='mean_squared_error')

    xs = np.array([-1.0, 0.0, 1.0, 2.0, 3.0, 4.0], dtype=float)
    ys = np.array([-2.0, 1.0, 4.0, 7.0, 10.0, 13.0], dtype=float)

    model.fit(xs, ys, epochs=50)
    mlflow.end_run()
    df = model.predict([10.0])
    f = open("training_ml_model.txt", "a")
    f.write(f"{os.environ['AIRFLOW_CTX_TASK_ID']}={int(df[0][0])}\n")
    f.close()
    return int(df[0][0])
    
def _choose_best_model():
    file_values = _read_file("training_ml_model.txt")
    best_key = max(file_values, key=file_values.get)
    if int(file_values[best_key]) > 30:
        return 'accurate' # task_id
    else:
        return 'inaccurate' # task_id


DAG_ID = "training_ml_model"
with DAG(
    DAG_ID, 
    start_date=datetime(2021, 5, 19),
    schedule_interval="@daily",
    description='Выбор лучшей модели.',
    catchup=False    
) as dag:
    with open(f'dags/{DAG_ID}.requirements.txt', 'r') as f:
        requirements = f.read().strip().split('\n')

    training_model_A = PythonVirtualenvOperator(
        task_id="training_model_A",
        python_callable=_training_model,
        requirements=requirements
    )

    training_model_B = PythonVirtualenvOperator(
        task_id="training_model_B",
        python_callable=_training_model,
        requirements=requirements
    )

    training_model_C = PythonVirtualenvOperator(
        task_id="training_model_C",
        python_callable=_training_model,
        requirements=requirements
    )

    choose_best_model = BranchPythonOperator(
        task_id="choose_best_model",
        python_callable=_choose_best_model
    )

    accurate = BashOperator(
        task_id="accurate",
        bash_command="echo 'accurate'"
    )

    inaccurate = BashOperator(
        task_id="inaccurate",
        bash_command="echo 'inaccurate'"
    )

    [training_model_A, training_model_B, training_model_C] >> choose_best_model >> [accurate, inaccurate]
