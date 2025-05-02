#!/bin/bash

# Strict mode
set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Variables
PROJECT_DIR="/opt/StarBurger"
VENV_PATH="/root/venv/bin/activate"
SERVICE_NAME="StarBurger.service"

# Load environment variables if .env exists
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -v '^#' $PROJECT_DIR/.env | xargs)
fi

echo -e "${GREEN}>>> Начинаем деплой StarBurger${NC}"

# 1. Обновляем код из Git
echo -e "${GREEN}>>> Получаем изменения из Git${NC}"
cd $PROJECT_DIR
git fetch
git reset --hard origin/master

# 2. Активируем virtualenv
echo -e "${GREEN}>>> Активируем virtualenv${NC}"
source $VENV_PATH

# 3. Устанавливаем Python-зависимости
echo -e "${GREEN}>>> Устанавливаем Python-зависимости${NC}"
pip install -U pip
pip install -r requirements.txt

# 4. Устанавливаем Node.js зависимости (если нужно)
if [ -f "$PROJECT_DIR/package.json" ]; then
    echo -e "${GREEN}>>> Устанавливаем Node.js зависимости${NC}"
    npm ci --dev
fi

# 5. Собираем фронтенд (если нужно)
if [ -f "$PROJECT_DIR/webpack.config.js" ]; then
    echo -e "${GREEN}>>> Собираем фронтенд${NC}"
    npm run build
fi

# 6. Применяем миграции
echo -e "${GREEN}>>> Применяем миграции БД${NC}"
python manage.py migrate --noinput

# 7. Собираем статику Django
echo -e "${GREEN}>>> Собираем статику Django${NC}"
python manage.py collectstatic --noinput --clear

# 8. Перезапускаем сервисы
echo -e "${GREEN}>>> Перезапускаем сервисы${NC}"
systemctl restart $SERVICE_NAME
systemctl reload nginx.service

echo -e "${GREEN}>>> Деплой успешно завершен!${NC}"

# Уведомляем Rollbar о деплое
echo -e "${GREEN}>>> Уведомляем Rollbar о деплое${NC}"
ROLLBAR_ACCESS_TOKEN="${TOKEN_ROLLBAR_PROD:-}"
if [ -z "$ROLLBAR_ACCESS_TOKEN" ]; then
  echo -e "${YELLOW}>>> Предупреждение: Rollbar access token не найден, пропускаем уведомление${NC}"
else
  LOCAL_USERNAME=$(whoami)
  CURRENT_COMMIT=$(git rev-parse HEAD)
  COMMENT="Deployed via deploy_star_burger.sh"
  ENVIRONMENT="production"
  
  echo -e "${GREEN}>>> Отправляем уведомление в Rollbar (коммит: ${CURRENT_COMMIT})${NC}"
  
  RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" https://api.rollbar.com/api/1/deploy/ \
    -F "access_token=$ROLLBAR_ACCESS_TOKEN" \
    -F "environment=$ENVIRONMENT" \
    -F "revision=$CURRENT_COMMIT" \
    -F "local_username=$LOCAL_USERNAME" \
    -F "comment=$COMMENT" \
    -F "status=succeeded" 2>&1)
  
  HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | sed 's/.*HTTP_STATUS://')
  BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS:/d')
  
  if [ "$HTTP_STATUS" -eq 200 ]; then
    echo -e "${GREEN}>>> Rollbar успешно уведомлен о деплое${NC}"
  else
    echo -e "${YELLOW}>>> Предупреждение: Не удалось уведомить Rollbar (HTTP $HTTP_STATUS)${NC}"
    echo -e "${YELLOW}>>> Ответ сервера: $BODY${NC}"
  fi
fi
