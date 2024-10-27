from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from plugins.hooks.jupyter_hook import JupyterHook
from plugins.operators.JupyterNotebookOperator import JupyterNotebookOperator

def execute_notebook(**context):
    hook = JupyterHook(jupyter_conn_id='notebook_default')
    result = hook.execute_notebook('notebooks/notebookTest.ipynb')
    
    # 결과 로깅
    if result.get('notebook_output'):
        context['task_instance'].xcom_push(
            key='notebook_output',
            value=result['notebook_output']
        )
    
    return result

with DAG(
    'remote_notebook_dag',
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,  # 수동 실행
    catchup=False
) as dag:

    notebook_task = PythonOperator(
        task_id='run_notebook',
        python_callable=execute_notebook,
        provide_context=True
    )

    # notebook_operator = JupyterNotebookOperator(
    #     task_id='run_notebook_with_operator',
    #     notebook_path='notebooks/notebookTest.ipynb',
    #     jupyter_conn_id='notebook_default'
    # )

    # notebook_task >> notebook_operator
