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
```
создать и активировать вируальное окружение ```python```
```bash
python3.9 -m venv env && source env/bin/activate
```
установить зависимости 
```bash
pip install -r requirements.txt
```
