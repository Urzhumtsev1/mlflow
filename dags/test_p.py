from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import BranchPythonOperator, PythonVirtualenvOperator


def _training_model(): 
    import os
    from random import randint
    val = randint(29, 32)
    f = open("training_ml_model2.txt", "a")
    f.write(f"{os.environ['AIRFLOW_CTX_TASK_ID']}={val}\n")
    f.close()
    return val
    

def _read_file(file_name):
    file_values = {}
    with open(file_name) as input_file:
        for line in input_file.readlines():
            line = line.strip()
            if "=" in line and not line.startswith("#") and not line.startswith("\n"):
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip("\"'")
                file_values[key] = value
    return file_values

def _choose_best_model():
    f = open('training_ml_model2.txt')
    print(f.read())
    file_values = _read_file("training_ml_model2.txt")
    print(file_values)
    best_key = max(file_values, key=file_values.get)
    if int(file_values[best_key]) > 30:
        return 'accurate' # task_id
    else:
        return 'inaccurate' # task_id

with DAG(
    "training_ml_model2", 
    start_date=datetime(2021, 5, 19),
    schedule_interval="@daily",
    description='Выбор лучшей модели.',
    catchup=False    
) as dag:

    
    training_model_A = PythonVirtualenvOperator(
        task_id="training_model_A",
        python_callable=_training_model,
    )

    training_model_B = PythonVirtualenvOperator(
        task_id="training_model_B",
        python_callable=_training_model,
    )

    training_model_C = PythonVirtualenvOperator(
        task_id="training_model_C",
        python_callable=_training_model,
    )

    choose_best_model = BranchPythonOperator(
        task_id="choose_best_model",
        python_callable=_choose_best_model
    )

    accurate = BashOperator(
        task_id="accurate",
        bash_command="echo 'accurate'"
    )

    inaccurate = BashOperator(
        task_id="inaccurate",
        bash_command="echo 'inaccurate'"
    )

    [training_model_A, training_model_B, training_model_C] >> choose_best_model >> [accurate, inaccurate]




# from airflow.operators.python_operator import PythonVirtualenvOperator # для своего плагина
# from airflow.utils.decorators import apply_defaults


# class MLPythonVirtualenvOperator(PythonVirtualenvOperator):
#         def func(f): return f
        
#         @apply_defaults
#         def __init__(
#             self, 
#             *, 
#             python_callable = func, 
#             task_id,
#             requirements = None, 
#             python_version = None, 
#             use_dill = False, 
#             system_site_packages = True, 
#             op_args = None, 
#             op_kwargs = None, 
#             string_args = None, 
#             templates_dict = None, 
#             templates_exts = None, 
#             **kwargs
#         ):
#             super().__init__(
#                 python_callable=python_callable, task_id=task_id, requirements=requirements,
#                 python_version=python_version, use_dill=use_dill, system_site_packages=system_site_packages, 
#                 op_args=op_args, op_kwargs=op_kwargs, string_args=string_args, templates_dict=templates_dict, 
#                 templates_exts=templates_exts, **kwargs)
#             self.requirements=["mlflow==1.16.0", "python-dotenv==0.17.1", "tensorflow"]
        
#         def __call__(cls, python_callable, task_id):
#             cls.python_callable = python_callable
#             cls.task_id = task_id
#             return cls