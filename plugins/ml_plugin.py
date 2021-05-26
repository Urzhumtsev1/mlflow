# import inspect
# import os
# import pickle
# import sys
# import types
# from tempfile import TemporaryDirectory
# from textwrap import dedent
# from typing import Any, Callable, Dict, Iterable, List, Optional, Union

# import dill

# from airflow.exceptions import AirflowException
# from airflow.utils.decorators import apply_defaults
# from airflow.utils.process_utils import execute_in_subprocess
# from airflow.utils.python_virtualenv import prepare_virtualenv, write_python_script
# from airflow.operators.python import PythonOperator
# from airflow.utils.decorators import apply_defaults


# class PythonMLOperator(PythonOperator):

#     BASE_SERIALIZABLE_CONTEXT_KEYS = {
#         'ds_nodash',
#         'inlets',
#         'next_ds',
#         'next_ds_nodash',
#         'outlets',
#         'params',
#         'prev_ds',
#         'prev_ds_nodash',
#         'run_id',
#         'task_instance_key_str',
#         'test_mode',
#         'tomorrow_ds',
#         'tomorrow_ds_nodash',
#         'ts',
#         'ts_nodash',
#         'ts_nodash_with_tz',
#         'yesterday_ds',
#         'yesterday_ds_nodash',
#     }
#     PENDULUM_SERIALIZABLE_CONTEXT_KEYS = {
#         'execution_date',
#         'next_execution_date',
#         'prev_execution_date',
#         'prev_execution_date_success',
#         'prev_start_date_success',
#     }
#     AIRFLOW_SERIALIZABLE_CONTEXT_KEYS = {'macros', 'conf', 'dag', 'dag_run', 'task'}

#     @apply_defaults
#     def __init__(  # pylint: disable=too-many-arguments
#         self,
#         *,
#         python_callable: Callable,
#         requirements: Optional[Iterable[str]] = ["mlflow==1.16.0"],
#         python_version: Optional[Union[str, int, float]] = None,
#         use_dill: bool = False,
#         system_site_packages: bool = True,
#         op_args: Optional[List] = None,
#         op_kwargs: Optional[Dict] = None,
#         string_args: Optional[Iterable[str]] = None,
#         templates_dict: Optional[Dict] = None,
#         templates_exts: Optional[List[str]] = None,
#         **kwargs,
#     ):
#         if (
#             not isinstance(python_callable, types.FunctionType)
#             or isinstance(python_callable, types.LambdaType)
#             and python_callable.__name__ == "<lambda>"
#         ):
#             raise AirflowException('PythonVirtualenvOperator only supports functions for python_callable arg')
#         if (
#             python_version
#             and str(python_version)[0] != str(sys.version_info.major)
#             and (op_args or op_kwargs)
#         ):
#             raise AirflowException(
#                 "Passing op_args or op_kwargs is not supported across different Python "
#                 "major versions for PythonVirtualenvOperator. Please use string_args."
#             )
#         super().__init__(
#             python_callable=python_callable,
#             op_args=op_args,
#             op_kwargs=op_kwargs,
#             templates_dict=templates_dict,
#             templates_exts=templates_exts,
#             **kwargs,
#         )
#         self.requirements = list(requirements or [])
#         self.string_args = string_args or []
#         self.python_version = python_version
#         self.use_dill = use_dill
#         self.system_site_packages = system_site_packages
#         if not self.system_site_packages and self.use_dill and 'dill' not in self.requirements:
#             self.requirements.append('dill')
#         self.pickling_library = dill if self.use_dill else pickle

#     def execute(self, context: Dict):
#         serializable_context = {key: context[key] for key in self._get_serializable_context_keys()}
#         super().execute(context=serializable_context)

#     def execute_callable(self):
#         with TemporaryDirectory(prefix='venv') as tmp_dir:
#             if self.templates_dict:
#                 self.op_kwargs['templates_dict'] = self.templates_dict

#             input_filename = os.path.join(tmp_dir, 'script.in')
#             output_filename = os.path.join(tmp_dir, 'script.out')
#             string_args_filename = os.path.join(tmp_dir, 'string_args.txt')
#             script_filename = os.path.join(tmp_dir, 'script.py')

#             prepare_virtualenv(
#                 venv_directory=tmp_dir,
#                 python_bin=f'python{self.python_version}' if self.python_version else None,
#                 system_site_packages=self.system_site_packages,
#                 requirements=self.requirements,
#             )

#             self._write_args(input_filename)
#             self._write_string_args(string_args_filename)
#             write_python_script(
#                 jinja_context=dict(
#                     op_args=self.op_args,
#                     op_kwargs=self.op_kwargs,
#                     pickling_library=self.pickling_library.__name__,
#                     python_callable=self.python_callable.__name__,
#                     python_callable_source=dedent(inspect.getsource(self.python_callable)),
#                 ),
#                 filename=script_filename,
#             )

#             execute_in_subprocess(
#                 cmd=[
#                     f'{tmp_dir}/bin/python',
#                     script_filename,
#                     input_filename,
#                     output_filename,
#                     string_args_filename,
#                 ]
#             )

#             return self._read_result(output_filename)

#     def _write_args(self, filename):
#         if self.op_args or self.op_kwargs:
#             with open(filename, 'wb') as file:
#                 self.pickling_library.dump({'args': self.op_args, 'kwargs': self.op_kwargs}, file)

#     def _get_serializable_context_keys(self):
#         def _is_airflow_env():
#             return self.system_site_packages or 'apache-airflow' in self.requirements

#         def _is_pendulum_env():
#             return 'pendulum' in self.requirements and 'lazy_object_proxy' in self.requirements

#         serializable_context_keys = self.BASE_SERIALIZABLE_CONTEXT_KEYS.copy()
#         if _is_airflow_env():
#             serializable_context_keys.update(self.AIRFLOW_SERIALIZABLE_CONTEXT_KEYS)
#         if _is_pendulum_env() or _is_airflow_env():
#             serializable_context_keys.update(self.PENDULUM_SERIALIZABLE_CONTEXT_KEYS)
#         return serializable_context_keys

#     def _write_string_args(self, filename):
#         with open(filename, 'w') as file:
#             file.write('\n'.join(map(str, self.string_args)))

#     def _read_result(self, filename):
#         if os.stat(filename).st_size == 0:
#             return None
#         with open(filename, 'rb') as file:
#             try:
#                 return self.pickling_library.load(file)
#             except ValueError:
#                 self.log.error(
#                     "Error deserializing result. Note that result deserialization "
#                     "is not supported across major Python versions."
#                 )
#                 raise