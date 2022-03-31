

1. systemd service

cp jupyterhub.service /etc/systemd/system/
systemctl daemon-reload

2. etc config files

mkdir /etc/jupyterhub
cp -r etc_jupyterhub/* /etc/jupyterhub/

3. create SSL keys

mkdir /etc/jupyterhub/ssl
openssl req -x509 -newkey rsa:4096 -keyout /etc/jupyterhub/ssl/key.pem -out /etc/jupyterhub/ssl/cert.pem -sha256 -nodes

4. enable and start service

systemctl enable --now jupyterhub

5. check https://<ip-or-domain>:8000


