import mlflow
import mlflow.keras
import mlflow.tensorflow
import numpy as np
import tensorflow as tf
from mlflow.exceptions import MlflowException
from tensorflow import keras

from config import URI

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

# print(model.predict([10.0]))

mlflow.end_run()


# mlflow models build-docker -m "s3://mlflow/artifacts/exp_1/6863a1daf71f4f608569cb038a500f6d/artifacts/model" -n "mlflow-test-model"

# curl http://127.0.0.1:5001/invocations -H 'Content-Type: application/json' -d '{
#     "data": [10.0]
# }'
