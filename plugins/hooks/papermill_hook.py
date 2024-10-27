# plugins/hooks/papermill_hook.py
from airflow.hooks.base import BaseHook
import requests
import os
from typing import Dict, Any
import json

class JupyterError(Exception):
    """Jupyter 관련 모든 에러의 기본 클래스"""
    def __init__(self, public_message: str, internal_message: str = None):
        self.public_message = public_message
        self.internal_message = internal_message or public_message
        super().__init__(self.public_message)


class ServerError(JupyterError):
    """서버 연결 관련 에러"""
    pass

class NotebookError(JupyterError):
    """노트북 실행 관련 에러"""
    def __init__(self, notebook_error: Dict[str, Any]):
        self.notebook_error = notebook_error
        super().__init__(
            public_message=self._format_error_message(notebook_error.get('message', '')),
            internal_message=notebook_error.get('message', '')
        )
    
    def _format_error_message(self, message: str) -> str:
        """노트북 에러 메시지에서 실제 에러 메시지만 추출"""
        try:
            # 마지막 에러 메시지 추출
            if '\n' in message:
                error_lines = [line for line in message.split('\n') if line.strip()]
                return error_lines[-1].strip()
            return message.strip()
        except Exception:
            return "노트북 실행 중 에러가 발생했습니다"

class PapermillHook(BaseHook):
    """Papermill을 실행하기 위한 Hook"""
    
    conn_name_attr = 'jupyter_conn_id'  # connection ID 속성 이름 지정
    default_conn_name = 'jupyter_default'  # 기본 connection ID
    conn_type = 'jupyter'  # connection 타입
    hook_name = 'Jupyter'  # hook 이름

    def __init__(self, jupyter_conn_id: str = default_conn_name) -> None:
        """
        Args:
            jupyter_conn_id: Airflow connection ID
        """
        super().__init__()
        self.jupyter_conn_id = jupyter_conn_id
        self.connection = self.get_connection(jupyter_conn_id)

    def execute_notebook(self, notebook_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            full_path = os.path.join('/opt/airflow/notebooks', notebook_path)
            base_url = f"http://{self.connection.host}:{self.connection.port}"
            url = f"{base_url}/papermill/execute"
            
            headers = {
                "Authorization": f"token {self.connection.password}",
                "Content-Type": "application/json"
            }
            
            data = {
                "notebook_path": full_path,
                "parameters": parameters
            }
            
            try:
                response = requests.post(url, headers=headers, json=data)
                
                if response.status_code in (401, 403):
                    raise ServerError("인증에 실패했습니다")
                
                response.raise_for_status()
                result = response.json()
                
                if result.get('status') == 'error':
                    raise NotebookError(result)
                
                return result
                
            except requests.exceptions.ConnectionError:
                raise ServerError("서버에 연결할 수 없습니다")
            except requests.exceptions.HTTPError:
                if response.status_code == 500:
                    try:
                        error_info = response.json()
                        if error_info.get('status') == 'error':
                            raise NotebookError(error_info)
                    except json.JSONDecodeError:
                        pass
                raise ServerError("서버에서 오류가 발생했습니다")
            
        except Exception as e:
            if isinstance(e, (NotebookError, ServerError)):
                raise
            raise ServerError("예기치 않은 오류가 발생했습니다")