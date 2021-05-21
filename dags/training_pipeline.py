from datetime import datetime


from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import BranchPythonOperator
from config import URI
from tensorflow import keras
from airflow.operators.python_operator import PythonVirtualenvOperator


def _training_model():
    import mlflow
    import mlflow.keras
    import mlflow.tensorflow
    import numpy as np
    import tensorflow as tf
    from mlflow.exceptions import MlflowException

    mlflow.set_tracking_uri(URI)
    EXPERIMENT = 'exp_1' # Задаем имя эксперименту

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

    model.fit(xs, ys, epochs=500)
    mlflow.end_run()
    df = model.predict([10.0])
    return df[0][0]

    

def _choose_best_model(ti):
    accuracies = ti.xcom_pull(
        task_ids=[
            "training_model_A",
            "training_model_B"
            "training_model_C"
        ]
    )
    best = max(accuracies)
    if best > 30:
        return 'accurate' # task_id
    else:
        return 'inaccurate' # task_id

with DAG(
    "training_ml_model", 
    start_date=datetime(2021, 5, 19),
    schedule_interval="@daily",
    description='Выбор лучшей модели.',
    catchup=False    
) as dag:

    training_model_A = PythonVirtualenvOperator(
        task_id="training_model_A",
        python_callable=_training_model
    )

    training_model_B = PythonVirtualenvOperator(
        task_id="training_model_B",
        python_callable=_training_model
    )

    training_model_C = PythonVirtualenvOperator(
        task_id="training_model_C",
        python_callable=_training_model
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