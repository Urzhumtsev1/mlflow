import mlflow
from config import URI

loaded_model = mlflow.pyfunc.load_model(f'models:/test_registration/1')

# Predict on a Pandas DataFrame.
import pandas as pd
df = loaded_model.predict(pd.DataFrame([3.], columns=['x']))
print(df)
# assert int(df[0].iloc[0]) == 30