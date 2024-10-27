from airflow import DAG
from datetime import datetime, timedelta
from plugins.operators.remote_papermill_operator import RemotePapermillOperator
import random

default_args = {
    'owner': 'airflow',
    'depends_on_past': False, 
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'papermill_analysis_dag',
    default_args=default_args,
    schedule_interval="*/3 * * * *", 
    catchup=False,
    description='A DAG that executes a Jupyter notebook using Papermill'
) as dag:

    analysis_task = RemotePapermillOperator(
        task_id='run_analysis',
        notebook_path='analysis.ipynb',
        parameters={
            # Jinja 템플릿을 사용하여 동적 파라미터 설정
            'start_date': '{{ (execution_date - macros.timedelta(days=30)).strftime("%Y-%m-%d") }}',
            'days': random.randint(15, 30),
            'sample_size': random.randint(1000, 5000),
            'random_seed': '{{ execution_date.int_timestamp | int }}',
            'category_weights': {'A': 0.5, 'B': 0.3, 'C': 0.2}
        },
        jupyter_conn_id='jupyter_default'
    )