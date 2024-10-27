from websocket import create_connection
import websocket

from airflow.hooks.base import BaseHook
import requests
import nbformat
import json
from typing import Any, Dict, Optional, List
import time
import logging
import threading
import queue
import uuid

logger = logging.getLogger(__name__)

class JupyterHook(BaseHook):
    """
    Jupyter 서버와 상호작용하기 위한 Hook
    
    :param jupyter_conn_id: Airflow connection ID (host, port, token 정보 포함)
    :param timeout: API 요청 타임아웃 (초)
    :param retry_limit: 재시도 횟수
    :param retry_delay: 재시도 간격 (초)
    """
    
    def __init__(
        self,
        jupyter_conn_id: str = 'notebook_default',
        timeout: int = 120,
        retry_limit: int = 3,
        retry_delay: int = 1
    ) -> None:
        super().__init__()
        self.jupyter_conn_id = jupyter_conn_id
        self.timeout = timeout
        self.retry_limit = retry_limit
        self.retry_delay = retry_delay
        self.base_url = None
        self.headers = None
        
    def get_conn(self) -> None:
        """Connection 정보로부터 API 접속 정보 설정"""
        conn = self.get_connection(self.jupyter_conn_id)
        
        # base_url에서 /lab 제거
        self.base_url = f"http://{conn.host}:{conn.port}"
        self.headers = {
            "Authorization": f"token {conn.password}",
            "Content-Type": "application/json"
        }
    
    def _make_request(
        self,
        endpoint: str,
        method: str = 'GET',
        data: Optional[Dict] = None
    ) -> Any:
        """
        API 요청 실행 (재시도 로직 포함)
        
        :param endpoint: API 엔드포인트
        :param method: HTTP 메서드
        :param data: 요청 데이터
        :return: API 응답
        """
        if not self.base_url:
            self.get_conn()
            
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.retry_limit):
            try:
                response = requests.request(
                    method,
                    url,
                    headers=self.headers,
                    json=data,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json() if response.content else None
                
            except requests.exceptions.RequestException as e:
                if attempt == self.retry_limit - 1:
                    raise Exception(f"Failed to execute request: {str(e)}")
                time.sleep(self.retry_delay)
    
    def test_connection(self) -> tuple[bool, str]:
        """Connection 테스트"""
        try:
            self.get_conn()
            self._make_request('/api/status')
            return True, "Successfully connected to Jupyter server"
        except Exception as e:
            return False, str(e)
        
    def execute_notebook(self, notebook_path: str) -> Dict:
        if not self.base_url:
            self.get_conn()

        try:
            # 1. 노트북 내용 가져오기
            notebook_url = f"{self.base_url}/api/contents/{notebook_path}"
            logger.info(f"Fetching notebook from: {notebook_url}")
            nb_response = requests.get(notebook_url, headers=self.headers)
            nb_response.raise_for_status()
            notebook = nb_response.json()

            # 2. 새 커널 생성
            kernel_response = requests.post(
                f"{self.base_url}/api/kernels",
                headers=self.headers
            )
            logger.info(f"Kernel creation response: {kernel_response.text}")
            kernel_response.raise_for_status()
            kernel_id = kernel_response.json()['id']

            try:
                # WebSocket 연결 설정
                ws_url = f"ws://{self.get_connection(self.jupyter_conn_id).host}:{self.get_connection(self.jupyter_conn_id).port}/api/kernels/{kernel_id}/channels"
                
                msg_queue = queue.Queue()
                
                def on_message(ws, message):
                    msg_queue.put(json.loads(message))

                def on_error(ws, error):
                    logger.error(f"WebSocket error: {error}")

                def on_close(ws, close_status_code, close_msg):
                    logger.info("WebSocket connection closed")

                # WebSocket 객체 생성
                websocket.enableTrace(True)
                ws = websocket.WebSocketApp(
                    ws_url,
                    header={"Authorization": f"token {self.get_connection(self.jupyter_conn_id).password}"},
                    on_message=on_message,
                    on_error=on_error,
                    on_close=on_close
                )

                # WebSocket 연결 시작
                ws_thread = threading.Thread(target=ws.run_forever)
                ws_thread.daemon = True
                ws_thread.start()

                # 연결 대기
                time.sleep(1)

                # 3. 각 코드 셀 실행
                results = []
                for cell in notebook['content']['cells']:
                    if cell['cell_type'] == 'code':
                        msg_id = str(uuid.uuid4())
                        execute_request = {
                            'header': {
                                'msg_id': msg_id,
                                'username': 'airflow',
                                'session': str(uuid.uuid4()),
                                'msg_type': 'execute_request',
                                'version': '5.0'
                            },
                            'parent_header': {},
                            'metadata': {},
                            'content': {
                                'code': cell['source'],
                                'silent': False,
                                'store_history': True,
                                'user_expressions': {},
                                'allow_stdin': False
                            },
                            'channel': 'shell'
                        }

                        logger.info(f"Executing cell: {cell['source'][:50]}...")
                        ws.send(json.dumps(execute_request))

                        # 결과 수집
                        outputs = self._collect_output(msg_queue, msg_id)
                        results.append({
                            'cell_source': cell['source'],
                            'outputs': outputs
                        })

                # 4. notebook_output 변수 획득
                final_msg_id = str(uuid.uuid4())
                final_request = {
                    'header': {
                        'msg_id': final_msg_id,
                        'username': 'airflow',
                        'session': str(uuid.uuid4()),
                        'msg_type': 'execute_request',
                        'version': '5.0'
                    },
                    'parent_header': {},
                    'metadata': {},
                    'content': {
                        'code': 'print(notebook_output)',
                        'silent': False,
                        'store_history': True,
                        'user_expressions': {},
                        'allow_stdin': False
                    },
                    'channel': 'shell'
                }

                ws.send(json.dumps(final_request))
                final_output = self._collect_output(msg_queue, final_msg_id)

                return {
                    'status': 'success',
                    'notebook_output': final_output,
                    'execution_results': results
                }

            finally:
                # WebSocket 연결 종료
                ws.close()
                
                # 커널 종료
                requests.delete(
                    f"{self.base_url}/api/kernels/{kernel_id}",
                    headers=self.headers
                )

        except Exception as e:
            logger.error(f"Failed to execute notebook: {str(e)}")
            raise Exception(f"Failed to execute notebook: {str(e)}")

    def _collect_output(self, msg_queue, msg_id, timeout=30):
        """WebSocket 메시지 큐에서 출력 수집"""
        outputs = []
        done = False
        start_time = time.time()
        
        while not done and (time.time() - start_time) < timeout:
            try:
                msg = msg_queue.get(timeout=0.5)
                if msg['parent_header'].get('msg_id') == msg_id:
                    if msg['msg_type'] in ['execute_result', 'display_data']:
                        outputs.append(msg['content'])
                    elif msg['msg_type'] == 'stream':
                        outputs.append(msg['content'])
                    elif msg['msg_type'] == 'status' and msg['content']['execution_state'] == 'idle':
                        done = True
            except queue.Empty:
                continue
                
        return outputs
