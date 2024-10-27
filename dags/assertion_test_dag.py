# dags/assertion_test_dag.py
from airflow import DAG
from plugins.operators.remote_papermill_operator import RemotePapermillOperator
from datetime import datetime, timedelta
import random

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,  # 재시도 없음
}

def generate_threshold():
    """임계값 생성 함수"""
    return random.randint(20, 40)  # 20-40 사이의 랜덤값 (30 기준으로 성공/실패 분기)

with DAG(
    'assertion_test_dag',
    default_args=default_args,
    schedule_interval='*/3 * * * *',  # 3분마다 실행
    catchup=False,
    description='DAG for testing assertion errors with random threshold'
) as dag:
    
    # 단일 태스크로 구성
    execute_notebook = RemotePapermillOperator(
        task_id='test_assertion',
        notebook_path='test_failure.ipynb',
        parameters={
            'threshold': generate_threshold(),  # 매번 랜덤값 생성
            'raise_error': True,
            'error_type': 'assertion'
        },
        do_xcom_push=False  # XCom 저장하지 않음
    )