import requests
import json

def execute_notebook(notebook_path, parameters):
    """
    Jupyter 서버의 Papermill endpoint를 호출하여 노트북 실행
    """
    url = "http://localhost:8888/papermill/execute"
    
    headers = {
        "Authorization": f"token airflow",  # JUPYTER_TOKEN과 동일한 값
        "Content-Type": "application/json"
    }
    
    data = {
        "notebook_path": notebook_path,
        "parameters": parameters
    }
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    
    return response.json()

# 실행 예시
try:
    result = execute_notebook(
        "/opt/airflow/notebooks/example.ipynb",
        {
            "start_date": "2024-01-01",
            "days": 30,
            "sample_size": 1000
        }
    )
    print("Execution result:", json.dumps(result, indent=2))
except Exception as e:
    print(f"Error executing notebook: {e}")