from setuptools import setup, find_packages

setup(
    name="papermill_ext",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "jupyter_server>=2.0.0",
        "papermill>=2.4.0",
        "nbformat",
        "nbclient",
        "ipykernel"
    ],
    # Jupyter Server Extension을 위한 entry point 추가
    entry_points={
        'jupyter_server.extensions': [
            'papermill_ext = papermill_ext:PapermillExtensionApp',
        ],
    },
)