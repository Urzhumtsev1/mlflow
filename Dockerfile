FROM python:3.7-slim-buster

RUN mkdir /mlflow/

RUN pip install mlflow boto3 psycopg2-binary tensorflow python-dotenv