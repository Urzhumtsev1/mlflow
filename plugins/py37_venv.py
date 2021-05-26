# from airflow.plugins_manager import AirflowPlugin
# from airflow.operators.python_operator import PythonVirtualenvOperator

# # def _generate_virtualenv_cmd(self, tmp_dir):
# #     cmd = ['python3.7','/usr/local/airflow/.local/lib/python3.7/site-packages/virtualenv', tmp_dir]
# #     if self.system_site_packages:
# #         cmd.append('--system-site-packages')
# #     if self.python_version is not None:
# #         cmd.append('--python=python{}'.format(self.python_version))
# #     return cmd

# def _generate_pip_install_cmd(tmp_dir, requirements):
#     requirements = [
#         "mlflow==1.16.0", "python-dotenv==0.17.1", "tensorflow"
#     ]
#     # direct path alleviates need to activate
#     cmd = [f'{tmp_dir}/bin/pip', 'install']
#     return cmd + requirements


# # PythonVirtualenvOperator._generate_virtualenv_cmd=_generate_virtualenv_cmd
# PythonVirtualenvOperator._generate_pip_install_cmd=_generate_pip_install_cmd

# class Python37VirtualenvOperator(PythonVirtualenvOperator): pass

# class EnvVarPlugin(AirflowPlugin):                
#     name = 'py37_venv'  