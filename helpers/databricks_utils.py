# helpers/databricks_utils.py
from functools import wraps
from helpers.constants import DATABRICKS_WORKSPACES, NOTEBOOK_IDS

def get_workspace_id(workspace_name):
    return DATABRICKS_WORKSPACES.get(workspace_name)

def get_notebook_id(notebook_name):
    return NOTEBOOK_IDS.get(notebook_name)

def get_seoul_yyyymm(ts):
    return ts.in_timezone("Asia/Seoul").strftime("%Y%m")

def get_seoul_yyyymmdd(ts):
    return ts.in_timezone("Asia/Seoul").strftime("%Y%m%d")

def get_seoul_yyyymmdd_HH(ts):
    return ts.in_timezone("Asia/Seoul").strftime("%Y%m%d %H")

def get_utc_yyyymm(ts):
    return ts.strftime("%Y%m")

def get_utc_yyyymmdd(ts):
    return ts.strftime("%Y%m%d")

def get_utc_yyyymmdd_HH(ts):
    return ts.strftime("%Y%m%d %H")

def extract_notebook_info(func):
    @wraps(func)
    def wrapper(**context):
        notebook_id = context['notebook_id']
        notebook_params = context['notebook_params']
        return func(notebook_id, notebook_params, **context)
    return wrapper