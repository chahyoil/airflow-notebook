FROM apache/airflow:2.10.2

USER root

# 필요한 시스템 패키지 설치
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3-dev \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


USER airflow

# Jupyter 관련 패키지 설치
RUN pip install --no-cache-dir \
    "apache-airflow==${AIRFLOW_VERSION}" \
    jupyterlab \
    papermill \
    nbformat \
    jupyter_server \
    ipykernel \
    nbclient

# Python 커널 설치
RUN python -m ipykernel install --user

# papermill extension 설치
COPY --chown=airflow:root jupyter_scripts /opt/airflow/jupyter_scripts
WORKDIR /opt/airflow/jupyter_scripts
RUN pip install --no-cache-dir -e .

# Extension 활성화
RUN mkdir -p /home/airflow/.jupyter && \
    jupyter server extension enable --py papermill_ext --sys-prefix

# Jupyter 설정
RUN echo "c.ServerApp.token = ''" >> /home/airflow/.jupyter/jupyter_server_config.py && \
    echo "c.ServerApp.password = ''" >> /home/airflow/.jupyter/jupyter_server_config.py && \
    echo "c.ServerApp.allow_origin = '*'" >> /home/airflow/.jupyter/jupyter_server_config.py && \
    echo "c.ServerApp.root_dir = '/opt/airflow/notebooks'" >> /home/airflow/.jupyter/jupyter_server_config.py

WORKDIR /opt/airflow

# 노트북 폴더 생성
RUN mkdir -p /opt/airflow/notebooks && \
    chown -R airflow:root /opt/airflow/notebooks