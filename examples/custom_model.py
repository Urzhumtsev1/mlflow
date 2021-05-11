# Пример как создать произвольную модель и пользоваться возможностями mlflow: Tracking, . 
from math import exp

import mlflow
from mlflow.models.signature import ModelSignature
from mlflow.types.schema import ColSpec, Schema

from config import URI

mlflow.set_tracking_uri(URI)

# Создание собственной произвольной модели
class MegaModel(mlflow.pyfunc.PythonModel):
    def __init__(self, lr, mega_param=42):
        self.lr = lr
        self.mega_param = mega_param
        self.__hidden = 1

    def predict(self, context, model_input):
        x = model_input
        return self._activate(x)

    def _activate(self, x):
        return self.__hidden / (1 + x**2)

    def fit(self, model_input, target):
        self.__hidden = len(model_input)
        return self

# Описание того, как будет выглядеть вход и выход модели.
input_scheme = Schema([ColSpec('double', 'x')])
output_scheme = Schema([ColSpec('double')])

signature = ModelSignature(inputs=input_scheme, outputs=output_scheme)

# Создание примера
input_example = {
    'x': 3.0
}

# Папка, в которую будет сохранена модель и различные конфиги.
model_path = 'testmodel'

# Обьявление тренировочных данных для модели.
model_input = [-1, 2, 3]
model_target = [0, 1, 1]

# Обьявление гиперпараметров.
lr = 1

# Тут начинается обучение модели.
with mlflow.start_run(run_name='test_run') as run:
    # Сохраням параметры, которые хотим отслеживать в mlflow ui.
    mlflow.log_param('lr', lr)

    # Инициализация и обучение модели.
    mm = MegaModel(lr)
    mm.fit(model_input, model_target)

    # Сохранение модели в виде артефакта и сопутсвующих конфигов.
    mlflow.pyfunc.log_model(
        artifact_path=model_path,
        python_model=mm,
        signature=signature,
        input_example=input_example,
        # registered_model_name='test_registration'
    )


# Для того чтобы создать докер образ модели, следует прописать следующую команду:
# mlflow models build-docker -m "runs:/some-run-uuid/my-model-dir" -n "my-image-name"
#
# Пример:
# mlflow models build-docker -m "s3://mlflow/artifacts/0/a2bc81a358564bd1ae0b7e28572e40d5/artifacts/testmodel" -n "mlflow-test-custom-model"
#
# Пример запроса к моделе:
# curl http://127.0.0.1:5001/invocations -H 'Content-Type: application/json' -d '{
#   "columns": [
#     "x"
#   ],
#   "data": [
#     [
#       3
#     ]
#   ]
# }'
# 
# Передаваемый с запросом json хранится как пример в input_example.json. Можно найти в информации об артефактах эксперимента.
