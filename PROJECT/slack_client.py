import slack_sdk as slack
import logging
import os
from pathlib import Path
from dotenv import load_dotenv #чтобы забрать SLACK_TOKEN из env файла

env_path = Path(".") / ".env" #указываем путь к env файлу
load_dotenv(dotenv_path=env_path) #загружаем env файл

BOT_TOKEN = os.environ["BOT_TOKEN"]
if not BOT_TOKEN:
    logging.error("Bot token not found in env vars")
    exit(1)

client = slack.WebClient(token=BOT_TOKEN)

def get_client():
    return client

def get_bot_id():
    return client.api_call("auth.test")["user_id"]