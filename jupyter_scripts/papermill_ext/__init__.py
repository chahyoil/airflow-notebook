# jupyter_scripts/papermill_ext/__init__.py
from jupyter_server.base.handlers import url_path_join
from .handlers import NotebookExecuteHandler
from jupyter_server.extension.application import ExtensionApp

class PapermillExtensionApp(ExtensionApp):
    def initialize_settings(self):
        self.settings.update({
            'base_url': self.serverapp.base_url,
        })

    def initialize_handlers(self):
        self.handlers.extend([
            (url_path_join(self.settings['base_url'], '/papermill/execute'), 
             NotebookExecuteHandler)
        ])

# Jupyter Server가 찾을 Extension Point
def _jupyter_server_extension_points():
    return [{
        "module": "papermill_ext",
        "app": PapermillExtensionApp
    }]

# 이전 버전 호환성을 위한 로더
def _load_jupyter_server_extension(server_app):
    server_app.log.info("Loading papermill_ext extension via legacy loader")
    web_app = server_app.web_app
    base_url = web_app.settings['base_url']
    
    web_app.add_handlers(
        ".*$", 
        [(url_path_join(base_url, '/papermill/execute'), NotebookExecuteHandler)]
    )
    
    server_app.log.info("Papermill extension loaded")
    return True