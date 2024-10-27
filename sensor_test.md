# Airflow DAG Sensor 테스트 결과

## 1. 기본 의존성 (dag1 -> dag2) 테스트

### 시나리오 1: dag2가 schedule_interval이 없는 경우
```python
dag1: schedule_interval = "0 8 * * *"  # 매일 8시
dag2: schedule_interval = None
```
**결과**: dag2 실행 안됨 (sensor가 dag1의 execution_date를 찾을 수 없음)

### 시나리오 2: 동일한 schedule_interval
```python
dag1: schedule_interval = "0 8 * * *"  # 매일 8시
dag2: schedule_interval = "0 8 * * *"  # 매일 8시
```
**결과**: 정상 실행 (권장되는 설정)

### 시나리오 3: 근소한 시간 차이
```python
dag1: schedule_interval = "0 8 * * *"   # 매일 8시
dag2: schedule_interval = "1 8 * * *"   # 매일 8시 1분
```
**결과**: dag2 무한 대기 (schedule_interval 일치하지 않음)

### 시나리오 4: 큰 시간 차이
```python
dag1: schedule_interval = "0 8 * * *"   # 매일 8시
dag2: schedule_interval = "0 9 * * *"   # 매일 9시

# execution_date_fn으로 해결
def adjust_execution_date(execution_date):
    return execution_date - timedelta(hours=1)

sensor = ExternalTaskSensor(
    execution_date_fn=adjust_execution_date
    ...
)
```
**결과**: execution_date_fn으로 조정하여 정상 실행

## 2. 3단계 의존성 테스트 (dag1 -> dag2 -> dag3)

### 케이스 1: TriggerDagRunOperator 사용
```python
dag1: schedule_interval = "0 8 * * *"
dag2: schedule_interval = None          # TriggerDagRunOperator로 실행
dag3: schedule_interval = "0 8 * * *"   # dag1과 동일
```
**결과**: 정상 실행 (dag2가 dag1의 logical_date 상속)

### 케이스 2: dag3가 schedule 없는 경우
```python
dag1: schedule_interval = "0 8 * * *"
dag2: schedule_interval = None          # TriggerDagRunOperator로 실행
dag3: schedule_interval = None
```
**결과**: dag3 실행 실패 (dag1의 logical_date와 불일치)

### 케이스 3: 시간차 실행
```python
dag1: schedule_interval = "50 7 * * *"  # 7시 50분
dag2: schedule_interval = "0 8 * * *"   # 8시
dag3: schedule_interval = "10 8 * * *"  # 8시 10분

# 각 sensor에서 사용할 execution_date_fn
def minus_10_minutes(execution_date):
    return execution_date - timedelta(minutes=10)
```
**결과**: execution_date_fn으로 10분씩 조정하여 정상 실행

## 3. 다중 의존성 테스트
```python
[dag1, dag2, dag3] >> dag4
모든 DAG: schedule_interval = "0 8 * * *"
```
**결과**: 정상 실행 (모든 DAG가 같은 schedule_interval)

## ExternalTaskSensor 주요 설정

### external_task_id
- None으로 설정 시: 앞선 DAG의 모든 task 완료 대기
- 특정 task_id 지정 시: 해당 task만 완료 대기

### mode 설정
```python
mode='poke'        # 워커 슬롯 계속 점유
mode='reschedule'  # 확인 실패시 슬롯 반환 (권장)
```

## 권장 사항
    1. 의존성 있는 DAG들은 동일한 schedule_interval 사용
    2. 시간차가 필요한 경우 execution_date_fn 활용
    3. schedule_interval = None 사용 지양
    4. sensor는 mode='reschedule' 권장
    5. 적절한 timeout 설정으로 무한 대기 방지