# 1. With Docker

## Build
  docker build -t expenses-bot .

## Start container
  docker run -d --name expenses-bot \
    -v $(pwd)/data:/app/data \
    --env-file .env \
    expenses-bot

## Check logs
  docker logs -f expenses-bot

# 2. With docker-compose

## Start
  docker-compose up -d

## Stop
  docker-compose down

## Check logs
  docker-compose logs -f

# 3. Pure start
  python bot.py

## You have to type ***/start*** again every time when you clear DB. **This will add you to users database** and everything will work fine
