import mlflow
logged_model = 's3://mlflow/artifacts/exp_1/6863a1daf71f4f608569cb038a500f6d/artifacts/model'

# Load model as a PyFuncModel.
loaded_model = mlflow.pyfunc.load_model(logged_model)

# Predict on a Pandas DataFrame.
import pandas as pd
loaded_model.predict(pd.DataFrame([10.0]))