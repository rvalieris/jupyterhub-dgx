

## Configuration

[JupyterHub docs](https://jupyterhub.readthedocs.io/en/stable/index.html)

### allowed users
list of users that are allowed to login

`c.Authenticator.allowed_users` on `/etc/jupyterhub/jupyterhub_config.py`

### admin users
list of users that are allowed to use the admin panel

`c.Authenticator.admin_users` on `/etc/jupyterhub/jupyterhub_config.py`

### container whilelist
list of containers that can be launched as a notebook

`/etc/jupyterhub/container_whitelist.tsv`

### SSL keys
SSL keys used by the web interface

`/etc/jupyterhub/ssl`

### Monitoring
see https://jupyterhub.readthedocs.io/en/stable/reference/monitoring.html

### Job submitting Form

`PyxisFormSpawner` on `/etc/jupyterhub/ext/dgxext.py`
