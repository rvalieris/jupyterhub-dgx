FROM jupyterhub/jupyterhub:2.2.2

RUN apt-get update && \
  apt-get install -y sudo libmunge2 && \
  pip install --no-cache-dir batchspawner==1.1 && \
  rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["jupyterhub", "-f", "/etc/jupyterhub/jupyterhub_config.py"]
