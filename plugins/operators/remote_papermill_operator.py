# plugins/operators/remote_papermill_operator.py
from airflow.models.baseoperator import BaseOperator
from airflow.utils.decorators import apply_defaults
from plugins.hooks.papermill_hook import PapermillHook, NotebookError, ServerError
from typing import Dict, Any
import logging
from airflow.exceptions import AirflowException, AirflowFailException  

logger = logging.getLogger(__name__)

class RemotePapermillOperator(BaseOperator):
    template_fields = ('parameters',)

    @apply_defaults
    def __init__(
        self,
        *,  # 키워드 전용 인자 강제
        notebook_path: str,
        parameters: Dict[str, Any] = None,
        jupyter_conn_id: str = 'jupyter_default',
        **kwargs
    ) -> None:
        """
        Args:
            notebook_path: 실행할 노트북의 상대 경로
            parameters: 노트북에 전달할 파라미터 딕셔너리
            jupyter_conn_id: Jupyter 서버 연결 ID
        """
        super().__init__(**kwargs)
        self.notebook_path = notebook_path
        self.parameters = parameters or {}
        self.jupyter_conn_id = jupyter_conn_id
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logger.info(f"노트북 실행 시작: {self.notebook_path}")
            logger.info(f"파라미터: {self.parameters}")
            
            hook = PapermillHook(jupyter_conn_id=self.jupyter_conn_id)
            result = hook.execute_notebook(
                notebook_path=self.notebook_path,
                parameters=self.parameters
            )
            
            logger.info("노트북 실행 완료")
            return {
                'status': 'success',
                'output': result.get('output', {})
            }
            
        except NotebookError as e:
            logger.error(f"노트북 실행 실패: {e.public_message}")
            raise AirflowFailException(e.public_message)
            
        except ServerError as e:
            logger.error("서버 오류가 발생했습니다")
            context['task_instance'].set_state('failed')
            raise AirflowFailException(e.public_message)
        
        except Exception as e:
            logger.error("예기치 않은 오류가 발생했습니다")
            raise AirflowFailException("예기치 않은 오류가 발생했습니다")