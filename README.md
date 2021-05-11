# mlflow

Добавить в ```~/.profile``` 
```bash
export MLFLOW_S3_ENDPOINT_URL="http://localhost:9000"
export AWS_ACCESS_KEY_ID="changeme"
export AWS_SECRET_ACCESS_KEY="changeme"
export MLFLOW_S3_IGNORE_TLS="true"
```
и активировать окружение 
```bash
source ~/.profile
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
```
создать и активировать вируальное окружение ```python```
```bash
python3.9 -m venv env && source env/bin/activate
```
установить зависимости 
```bash
pip install -r requirements.txt
```
поднять контейнеры
```bash
docker-compose up -d
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
