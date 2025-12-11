#!/bin/bash

echo "Starting fastapi backend server setup..."
sudo apt update
sudo apt install nginx -y
sudo apt install supervisor -y

sudo nginx
sudo supervisord

echo "Installation complete..."

echo "Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Creating environment files..."
echo "SUPABASE_URL=/api/" > .env
echo "SUPABASE_ANON_KEY=/api/" > .env
echo "SUPABASE_SERVICE_ROLE_KEY=/api/" > .env
echo "Environment files created..."

sudo bash -c 'cat > /etc/nginx/sites-available/default << '\''EOF'\''
server {
    listen 80;
    server_name YOUR_IP_ADDRESS;
    client_max_body_size 100M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript application/json;

    # Backend images - MUST come first before any regex matches
    location ^~ /images/ {
        proxy_pass http://127.0.0.1:8000/images/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # API Proxy
    location ^~ /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection '\''upgrade'\'';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeouts for large uploads
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
EOF'

echo "testing nginx configuration..."
sudo nginx -t

echo "restarting nginx..."
sudo nginx -s reload

echo "nginx done..."

echo "creating fastapi server..."
sudo bash -c 'cat > /etc/supervisor/conf.d/fastapi.conf << '\''EOF'\''
[program:fastapi]
directory=BACKEND_PATH
command=BACKEND_PATH/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
user=root
autostart=true
autorestart=true
stderr_logfile=/var/log/fastapi.err.log
stdout_logfile=/var/log/fastapi.out.log
environment=PATH="BACKEND_PATH/venv/bin"
EOF'

echo "restarting supervisor..."
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart fastapi
echo "fastapi server done..."x