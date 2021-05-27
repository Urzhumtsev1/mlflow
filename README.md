# mlflow & airflow

Установить Docker CE и Docker Compose **v1.27.0+**

Добавить в ```~/.profile``` 
```bash
export MLFLOW_S3_ENDPOINT_URL="http://localhost:9000"
export AWS_ACCESS_KEY_ID="changeme"
export AWS_SECRET_ACCESS_KEY="changeme"
export MLFLOW_S3_IGNORE_TLS="true"
export MLFLOW_TRACKING_URI="http://localhost:5000"
```
и активировать окружение 
```bash
source ~/.profile
```
```bash
mkdir ./dags ./logs ./plugins
```

колнировать проект и создать файл ```.env``` 
```bash
git clone git@github.com:Urzhumtsev1/mlflow.git && cd mlflow && touch .env
```
со следующим содержимым:
```bash
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changeme
PG_HOST=localhost
PG_PORT=5432
AWS_ACCESS_KEY_ID=changeme
AWS_SECRET_ACCESS_KEY=changeme
MINIO_ACCESS_KEY=changeme
MINIO_SECRET_KEY=changeme
MLFLOW_S3_ENDPOINT_URL=http://minio:9000
AIRFLOW__CORE__EXECUTOR=CeleryExecutor
AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://postgres:changeme@db/airflow
AIRFLOW__CELERY__RESULT_BACKEND=db+postgresql://postgres:changeme@db/airflow
AIRFLOW__CELERY__BROKER_URL=redis://:@redis:6379/0
AIRFLOW__CORE__FERNET_KEY=AVh9TstunFSoowrrgcGJ31hsjFmK0wFhs3BPdAmIxlc=
AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=true
AIRFLOW__CORE__LOAD_EXAMPLES=true
AIRFLOW__API__AUTH_BACKEND=airflow.api.auth.backend.basic_auth
_AIRFLOW_DB_UPGRADE=true
_AIRFLOW_WWW_USER_CREATE=true
_AIRFLOW_WWW_USER_USERNAME=airflow
_AIRFLOW_WWW_USER_PASSWORD=airflow
```
Установить ```AIRFLOW__CORE__LOAD_EXAMPLES=true``` если нужны примеры DAGов

еще немного переменных
```bash
echo -e "\nAIRFLOW_UID=$(id -u)\nAIRFLOW_GID=0" >> .env
```

создать и активировать вируальное окружение ```python```
```bash
python3.9 -m venv env && source env/bin/activate
```
установить зависимости 
```bash
pip install -r requirements.txt
```

создаем свой AIRFLOW__CORE__FERNET_KEY и меняем соответствующие значение в ```.env```
```bash
python -c "from cryptography.fernet import Fernet; FERNET_KEY = Fernet.generate_key().decode(); print(FERNET_KEY)"
```

установить пароль для mlflow
```bash
sudo apt install apache2-utils -y;
htpasswd -c config/nginx/.htpasswd mlflow
```
Во время выполнения команды будет предложено дважды ввести пароль пользователя mlflow

поднять контейнеры
```bash
docker-compose -f mlflow.docker-compose.yml -f airflow.docker-compose.yml up -d
```
после этого можно запускать эксперименты
```bash
python examples/ml_model.py
```
Трекинг сервис mlflow http://localhost:5000/

Объектное хранилище minio http://localhost:9000/minio/mlflow/

Собрать докер образ модели
```bash
mlflow models build-docker -m "s3://mlflow/artifacts/название_эксперимента/хэш_эксперимента/artifacts/model" -n "mlflow-test-model"
```
Поднять модель
```bash
docker run -p 5001:8080 "mlflow-test-model"
```
Обратиться к модели
```bash
curl http://127.0.0.1:5001/invocations -H 'Content-Type: application/json' -d '{
    "data": [10.0]
}'
```
