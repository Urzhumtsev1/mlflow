import mlflow

model_name = 'model_test'
stage = 'Staging'
logged_model = f'models:/{model_name}/{stage}'

# Load model as a PyFuncModel.
loaded_model = mlflow.pyfunc.load_model(logged_model)

# Predict on a Pandas DataFrame.
import pandas as pd
df = loaded_model.predict(pd.DataFrame([10.0]))

assert int(df[0].iloc[0]) == 30