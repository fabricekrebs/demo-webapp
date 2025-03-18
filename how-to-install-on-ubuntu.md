## How to install on a Ubuntu server 24.04

## Update package lists
```sh
sudo apt-get update
```

## Install necessary packages
```sh
sudo apt install gh python3-pip python3-venv nginx podman -y
```

## Configure container registries
```sh
sudo bash -c 'cat <<EOF > /etc/containers/registries.conf
[registries.search]
registries = ["docker.io"]
EOF'
```

## Run PostgreSQL container
> **Warning:** Ensure to modify this password, and define it in the .env file later in this guide.
```sh
sudo podman run \
  -p 5432:5432 \
  --name postgres \
  --network podman \
  -e POSTGRES_PASSWORD=mypassword \
  -d postgres:16.8
```

## Authenticate GitHub CLI
```sh
gh auth login
```

## Add a new user for gunicorn
```sh
sudo adduser --disabled-password --gecos "" gunicorn
```

## Navigate to /srv directory
```sh
cd /srv
```

## Create and set permissions for the demowebapp directory
```sh
sudo mkdir demowebapp
sudo chown $USER demowebapp
cd demowebapp/
```

## Clone the repository
```sh
gh repo clone https://github.com/fabricekrebs/demo-webapp.git .
```

## Set up Python virtual environment
```sh
python3 -m venv venv
```

## Activate virtual environment
```sh
source venv/bin/activate
```

## Install required Python packages
```sh
pip install -r requirements.txt
```

## Create gunicorn socket file
```sh
cat <<EOF >> /tmp/gunicorn.socket
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target
EOF
```

## Move gunicorn socket file to systemd directory
```sh
sudo mv /tmp/gunicorn.socket /etc/systemd/system/gunicorn.socket
```

## Create gunicorn service file
```sh
cat <<EOF >> /tmp/gunicorn.service
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
User=gunicorn
Group=www-data
WorkingDirectory=/srv/demowebapp
ExecStart=/srv/demowebapp/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/run/gunicorn.sock \
          demowebapp.wsgi

[Install]
WantedBy=multi-user.target
EOF
```

## Move gunicorn service file to systemd directory
```sh
sudo mv /tmp/gunicorn.service /etc/systemd/system/gunicorn.service
```

## Start and enable gunicorn socket
```sh
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
```

## Create nginx configuration file for the application
> **Warning:** Ensure to change the server_domain_or_IP with the correct external IP.
```sh
cat <<EOF >> /tmp/demowebapp
server {
    listen 80;
    server_name server_domain_or_IP;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /srv/demowebapp/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
EOF
```
## Move nginx configuration file to sites-available directory
```sh
sudo mv /tmp/demowebapp /etc/nginx/sites-available/demowebapp
```

## Enable the nginx site configuration
```sh
sudo ln -s /etc/nginx/sites-available/demowebapp /etc/nginx/sites-enabled
```

## Restart nginx to apply changes
```sh
sudo systemctl restart nginx
```

## Create environment variables file
> **Warning:** Adapt the file accordingly to your setup
```sh
cat <<EOF >> .env
SECRET_KEY=6515165131asdfasdfasd3f1s5df1sad23adsf
DEBUG=True
ALLOWED_HOSTS=*
BACKEND_ADDRESS=http://server_domain_or_IP:8000
TIME_ZONE=CET
CORS_ALLOW_ALL_ORIGINS=True
DB_USER=postgres
DB_PASSWORD=mypassword
DB_NAME=postgres
DB_HOST=localhost
DB_PORT=5432
EOF
```

## Restart gunicorn to apply changes
```sh
sudo systemctl restart gunicorn
```

## Apply database migrations
```sh
./manage.py makemigrations
./manage.py migrate
```

## Create a superuser for the application
```sh
./manage.py createsuperuser
```

The website should be accessible at the public address defined.