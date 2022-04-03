

## Manual Install

1. systemd service

```
cp jupyterhub-dgx.service /etc/systemd/system/
systemctl daemon-reload
```

2. config files

```
mkdir /etc/jupyterhub
cp -r etc_jupyterhub/* /etc/jupyterhub/
```

3. SSL keys

```
mkdir /etc/jupyterhub/ssl

# only accessible by root
chmod 700 /etc/jupyterhub/ssl

# creates a self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout /etc/jupyterhub/ssl/key.pem -out /etc/jupyterhub/ssl/cert.pem -sha256 -nodes
```

4. enable and start service

```
# enable to run on boot
systemctl enable jupyterhub-dgx

# start, the first run will take longer
# because it is building the image
systemctl start jupyterhub-dgx
```

5. check status

```
systemctl status jupyterhub-dgx

# logs
journalctl -u jupyterhub-dgx

# webpage
https://<ip-or-domain>:8000
```

