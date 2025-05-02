#!/bin/bash

# Strict mode
set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}>>> Начинаем локальный деплой StarBurger${NC}"

# Build frontend
if [ -f "build_frontend.sh" ]; then
    echo -e "${GREEN}>>> Собираем фронтенд${NC}"
    bash build_frontend.sh
fi

# Collect Django static
echo -e "${GREEN}>>> Собираем статику Django${NC}"
python manage.py collectstatic --noinput

echo -e "${GREEN}>>> Локальный деплой успешно завершен!${NC}" 