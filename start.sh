#!/bin/bash

sudo docker compose down; sudo docker builder prune -f; sudo docker compose up -d --build

echo ""
echo -n "Generazione URL..."

while true; do
    URL=$(sudo docker compose logs tunnel 2>&1 | grep -oE "https://[a-zA-Z0-9-]+\.trycloudflare\.com" | head -n 1)

    if [ ! -z "$URL" ]; then
        echo -e "\rURL generato: $URL/login/"
        break
    fi

    sleep 0.5
done
