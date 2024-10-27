from airflow import DAG
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

# DAG 1
dag1 = DAG(
    'dag1',
    schedule_interval='0 8 * * *',  # 매일 08:00
    start_date=datetime(2024, 1, 1),
    catchup=False
)

def task1_function():
    print("DAG 1 Task 실행")

task1 = PythonOperator(
    task_id='task1',
    python_callable=task1_function,
    dag=dag1
)

# DAG 2
dag2 = DAG(
    'dag2',
    schedule_interval='1 8 * * *',  # 매일 08:01
    start_date=datetime(2024, 1, 1),
    catchup=False
)

sensor = ExternalTaskSensor(
    task_id='wait_for_dag1',
    external_dag_id='dag1',
    external_task_id='task1',
    timeout=3600,  # 1시간 후 timeout
    mode='reschedule',
    poke_interval=30,  # 1분마다 확인
    dag=dag2
)

def task2_function():
    print("DAG 2 Task 실행")

task2 = PythonOperator(
    task_id='task2',
    python_callable=task2_function,
    dag=dag2
)

sensor >> task2