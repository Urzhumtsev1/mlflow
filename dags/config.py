from dotenv import dotenv_values
# Настройка различных подключений mlflow
config = dotenv_values("dags/.env")
PG_USER=config['POSTGRES_USER']
PG_PASS=config['POSTGRES_PASSWORD']
PG_HOST=config['PG_HOST']
PG_PORT=config['PG_PORT']
PG_DB_NAME=config['PG_DATABASE_NAME']
APP_LOGIN=config['APP_LOGIN']
APP_PASS=config['APP_PASS']
APP_HOST=config['APP_HOST']
URL_FIRES = 'https://karta.yanao.ru/ags1/rest/services/DPRR/ags1_greenatom_fires/MapServer/0'

DB_URI=f"postgres://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_DB_NAME}"
