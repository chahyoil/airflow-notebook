# dags/remote_papermill_dag.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from plugins.operators.remote_papermill_operator import RemotePapermillOperator
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def process_result(**context):
    """결과 처리 함수"""
    ti = context['task_instance']
    result = ti.xcom_pull(key='execution_result', task_ids='execute_notebook')
    
    if not result:
        return "실행 결과를 찾을 수 없습니다."
    
    if result['status'] == 'error':
        error_message = result.get('error_message', '알 수 없는 에러')
        error_type = result.get('error_type', '알 수 없는 에러 타입')
        log_path = result.get('execution_log_path', '로그 경로 없음')
        return f"노트북 실행 중 에러 발생 - 타입: {error_type}, 메시지: {error_message}, 로그: {log_path}"
    
    output = result.get('output', {})
    logger.info(f"처리된 결과: {json.dumps(output, indent=2)}")
    return f"노트북 실행 성공: {json.dumps(output, indent=2)}"

with DAG(
    'test_failure_dag',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    description='DAG for executing notebooks using RemotePapermillOperator'
) as dag:
    
    # 노트북 실행 태스크
    execute_task = RemotePapermillOperator(
        task_id='execute_notebook',
        notebook_path='test_failure.ipynb',
        parameters={
            'threshold': '{{ dag_run.conf.get("threshold", 50) }}',
            'raise_error': '{{ dag_run.conf.get("raise_error", True) }}',
            'error_type': '{{ dag_run.conf.get("error_type", "value") }}'
        }
    )
    
    # 결과 처리 태스크
    process_task = PythonOperator(
        task_id='process_result',
        python_callable=process_result,
        provide_context=True
    )
    
    # 결과 알림 태스크
    notification_task = BashOperator(
        task_id='send_notification',
        bash_command='echo "Execution completed with result: {{ task_instance.xcom_pull(key="execution_result", task_ids="execute_notebook") }}"'
    )

    # 태스크 순서 설정
    execute_task >> process_task >> notification_task