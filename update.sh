#git stash
git pull
docker build --tag tasmota-exporter:latest .
chmod +x update.sh
docker-compose down
docker-compose up -d
