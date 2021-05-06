import numpy as np
import tensorflow as tf
from dotenv import dotenv_values
from tensorflow import keras

import mlflow
import mlflow.keras
import mlflow.tensorflow

config = dotenv_values(".env")
PG_USER=config['POSTGRES_USER']
PG_PASS=config['POSTGRES_PASSWORD']
PG_HOST=config['PG_HOST']
PG_PORT=config['PG_PORT']

uri=f"postgresql+psycopg2://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/mlflow"
mlflow.set_tracking_uri(uri)
mlflow.set_experiment('exp_1')
mlflow.tensorflow.autolog()
mlflow.keras.autolog()

mlflow.start_run()

model = tf.keras.Sequential([keras.layers.Dense(units=1, input_shape=[1])])

model.compile(optimizer='sgd', loss='mean_squared_error')

xs = np.array([-1.0, 0.0, 1.0, 2.0, 3.0, 4.0], dtype=float)
ys = np.array([-2.0, 1.0, 4.0, 7.0, 10.0, 13.0], dtype=float)

model.fit(xs, ys, epochs=500)

# print(model.predict([10.0]))

mlflow.end_run()
