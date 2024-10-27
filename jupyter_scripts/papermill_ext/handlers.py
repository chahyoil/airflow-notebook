# jupyter_scripts/papermill_ext/handlers.py
from jupyter_server.base.handlers import APIHandler
from tornado import web
import papermill as pm
import json
import os
import tempfile
from nbformat import read, write
from nbclient import NotebookClient
import logging
from datetime import datetime

class NotebookExecuteHandler(APIHandler):
    def setup_execution_logger(self):
        """노트북 실행을 위한 로거 설정"""
        logger = logging.getLogger('notebook_execution')
        logger.setLevel(logging.INFO)
        
        # 현재 시간을 이용한 로그 파일명 생성
        log_filename = f"notebook_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_path = os.path.join('/opt/airflow/logs', log_filename)
        
        # 파일 핸들러 추가
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.INFO)
        
        # 포맷터 설정
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        
        logger.addHandler(fh)
        return logger, log_path

    def capture_output(self, cell):
        """셀의 출력 결과를 캡처"""
        outputs = []
        if cell.get('outputs'):
            for output in cell['outputs']:
                if output.get('output_type') == 'stream':
                    outputs.append({
                        'type': 'stream',
                        'name': output.get('name', ''),
                        'text': output.get('text', '')
                    })
                elif output.get('output_type') == 'execute_result':
                    outputs.append({
                        'type': 'execute_result',
                        'data': output.get('data', {})
                    })
                elif output.get('output_type') == 'display_data':
                    outputs.append({
                        'type': 'display_data',
                        'data': output.get('data', {})
                    })
        return outputs
    
    def format_error_message(self, error_message: str) -> str:
        """에러 메시지에서 실제 에러 내용만 추출"""
        try:
            # 에러 메시지에서 마지막 줄(실제 에러 메시지)만 추출
            lines = [line for line in error_message.split('\n') if line.strip()]
            for line in reversed(lines):
                # AssertionError, ValueError 등으로 시작하는 라인 찾기
                if any(error_type in line for error_type in ['AssertionError:', 'ValueError:', 'KeyError:', 'TypeError:']):
                    return line.strip()
            # 못 찾은 경우 마지막 줄 반환
            return lines[-1].strip() if lines else error_message
        except Exception:
            return error_message

    @web.authenticated
    async def post(self):
        logger, log_path = self.setup_execution_logger()
        try:
            data = json.loads(self.request.body)
            notebook_path = data.get('notebook_path')
            parameters = data.get('parameters', {})

            logger.info(f"Starting notebook execution: {notebook_path}")
            logger.info(f"Parameters: {json.dumps(parameters, indent=2)}")

            if not os.path.exists(notebook_path):
                raise FileNotFoundError(f"Notebook not found: {notebook_path}")

            with tempfile.NamedTemporaryFile(suffix='.ipynb', delete=False) as tmp:
                output_path = tmp.name

            # 노트북 실행
            logger.info("Executing notebook with papermill")
            pm.execute_notebook(
                notebook_path,
                output_path,
                parameters=parameters,
                kernel_name='python3',
                progress_bar=False,
                request_save_on_cell_execute=True,
                execution_timeout=600,
                log_output=True  # 로그 출력 활성화
            )

            # 결과 읽기
            logger.info("Reading execution results")
            with open(output_path, 'r') as f:
                nb = read(f, as_version=4)
                
                # 각 셀의 실행 결과 캡처
                cell_outputs = []
                for i, cell in enumerate(nb.cells):
                    cell_result = {
                        'cell_index': i,
                        'cell_type': cell.get('cell_type'),
                        'execution_count': cell.get('execution_count'),
                        'outputs': self.capture_output(cell)
                    }
                    cell_outputs.append(cell_result)
                    
                    # 로그에 셀 실행 결과 기록
                    logger.info(f"Cell {i} execution result:")
                    logger.info(json.dumps(cell_result, indent=2))

                # notebook_output 찾기
                output = None
                for cell in nb.cells:
                    if cell.get('outputs'):
                        for output_item in cell['outputs']:
                            if output_item.get('output_type') == 'display_data' and \
                            'application/json' in output_item.get('data', {}):
                                output = output_item['data']['application/json']
                                break
                        if output:
                            break

            response = {
                'status': 'success',
                'output': output,  # 이제 JSON 형식의 출력이 포함됨
                'cell_outputs': cell_outputs,
                'execution_log_path': log_path
            }
            
            self.finish(response)

        except Exception as e:
            error_message = self.format_error_message(str(e))
            logger.error(f"Failed to execute notebook: {error_message}", exc_info=True)
            self.set_status(500)
            self.finish({
                'status': 'error',
                'message': error_message,
                'execution_log_path': log_path
            })

        finally:
            if 'output_path' in locals():
                try:
                    os.remove(output_path)
                except:
                    logger.error("Failed to remove temporary notebook file", exc_info=True)