from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from plugins.hooks.jupyter_hook import JupyterHook
from typing import Any, Dict, Optional

class JupyterNotebookOperator(BaseOperator):
    """
    Jupyter 노트북을 실행하는 Operator
    
    :param notebook_path: 실행할 노트북 경로
    :param parameters: 노트북에 전달할 파라미터
    :param jupyter_conn_id: Airflow connection ID
    :param timeout: 실행 타임아웃 (초)
    """
    
    @apply_defaults
    def __init__(
        self,
        notebook_path: str,
        parameters: Optional[Dict] = None,
        jupyter_conn_id: str = 'notebook_default',
        timeout: Optional[int] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self.notebook_path = notebook_path
        self.parameters = parameters
        self.jupyter_conn_id = jupyter_conn_id
        self.timeout = timeout
        
    def execute(self, context: Dict) -> Dict:
        hook = JupyterHook(jupyter_conn_id=self.jupyter_conn_id)
        
        # context에서 필요한 정보 파라미터에 추가
        if self.parameters is None:
            self.parameters = {}
        self.parameters.update({
            'execution_date': context['execution_date'].isoformat(),
            'run_id': context['run_id']
        })
        
        return hook.execute_notebook(
            notebook_path=self.notebook_path,
            parameters=self.parameters,
            timeout=self.timeout
        )