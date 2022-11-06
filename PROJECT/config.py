import logging
from pathlib import Path
from dotenv import load_dotenv #чтобы забрать SLACK_TOKEN из env файла
import os


class Config:
    bot_token = None
    sign_secret = None
    app_token = None

    def __init__(self):
        env_path = Path(".") / ".env" #указываем путь к env файлу
        load_dotenv(dotenv_path=env_path) #загружаем env файл

    def get_bot_token(self):
        if self.bot_token:
            return self.bot_token 

        bot_token = os.environ["BOT_TOKEN"]
        if not bot_token:
            logging.error("Bot token not found in env vars")
            exit(1)
        self.bot_token = bot_token
        return bot_token

    def get_sign_secret(self):
        if self.sign_secret:
            return self.sign_secret 

        sign_secret = os.environ["SIGNING_SECRET"]
        if not sign_secret:
            logging.error("Signing secret not found in env vars")
            exit(1)
        self.sign_secret = sign_secret
        return sign_secret

    def get_app_token(self):
        if self.app_token:
            return self.app_token 

        app_token = os.environ["APP_TOKEN"]
        if not app_token:
            logging.error("App token not found in env vars")
            exit(1)
        self.app_token = app_token
        return app_token