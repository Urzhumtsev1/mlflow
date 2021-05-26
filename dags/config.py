from dotenv import dotenv_values
# Настройка различных подключений mlflow
config = dotenv_values("dags/.env")
PG_USER=config['POSTGRES_USER']
PG_PASS=config['POSTGRES_PASSWORD']
PG_HOST=config['PG_HOST']
PG_PORT=config['PG_PORT']

URI=f"postgresql+psycopg2://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/mlflow"
