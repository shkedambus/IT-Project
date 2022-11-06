import os
import logging
import slack_sdk as slack
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from pymongo import MongoClient

from pathlib import Path
from dotenv import load_dotenv #чтобы забрать SLACK_TOKEN из env файла


env_path = Path(".") / ".env" #указываем путь к env файлу
load_dotenv(dotenv_path=env_path) #загружаем env файл


logging.basicConfig(level=logging.DEBUG)

BOT_TOKEN = os.environ["BOT_TOKEN"]
if not BOT_TOKEN:
    logging.error("Bot token not found in env vars")
    exit(1)

SIGNING_SECRET = os.environ["SIGNING_SECRET"]
if not SIGNING_SECRET:
    logging.error("Signing secret not found in env vars")
    exit(1)

APP_TOKEN = os.environ["APP_TOKEN"]
if not APP_TOKEN:
    logging.error("App token not found in env vars")
    exit(1)


app = App(
    token=BOT_TOKEN,
    signing_secret=SIGNING_SECRET
)
client = slack.WebClient(token=BOT_TOKEN)


#получаем id команды
TEAM_ID = client.api_call("auth.test")["team_id"]


#подключаем базу данных
CONNECTION_STRING = "mongodb+srv://shkedambus:foFtyWYD41DZrZT0@ivr.zbasqqs.mongodb.net/?retryWrites=true&w=majority"
cluster = MongoClient(CONNECTION_STRING)
db = cluster[TEAM_ID]


#получаем id бота и Jira, формируем коллекцию users
def on_start():
    if "id" not in db.list_collection_names():
        BOT_ID = client.api_call("auth.test")["user_id"]
        JIRA_ID = ""
        all_users = client.users_list()
        for member in all_users["members"]:
            if member["is_bot"] and member["real_name"] == "Jira":
                JIRA_ID = member["id"]
        db["id"].insert_one({"bot_id": BOT_ID, "jira_id": JIRA_ID})
    else:
        myquery = db["id"].find_one()
        BOT_ID = myquery["bot_id"]
        JIRA_ID = myquery["jira_id"]


    if "users" not in db.list_collection_names():
        support_team = []
        all_users = client.users_list()
        for member in all_users["members"]:
            if not member["is_bot"] and member["id"] != "USLACKBOT":
                support_team.append({"user": member["id"], "email": member["profile"]["email"], "notification": 24, "has_permission": False})
        db["users"].insert_many(support_team)
    

    return {"bot_id": BOT_ID, "jira_id": JIRA_ID} #возвращает словарь, содержащий id бота и id Jira (если есть)
result = on_start()
BOT_ID = result["bot_id"]
JIRA_ID = result["jira_id"]


import slack_actions, slack_commands, slack_events, slack_shortcuts, slack_views

#shortcuts
@app.shortcut("connect_jira")
def connect_jira(ack, payload):
    return slack_shortcuts.connect_jira(ack, payload)

@app.shortcut("sup_users")
def sup_users(ack, payload):
    return slack_shortcuts.sup_users(ack, payload)

@app.shortcut("select_emojis")
def select_emojis(ack, payload):
    return slack_shortcuts.select_emojis(ack, payload)

#views
@app.view("jira_1")
def jira_1(ack, body, view, logger):
    return slack_views.jira_1(ack, body, view, logger)

@app.view("jira_2")
def jira_2(ack, body, view, logger):
    return slack_views.jira_2(ack, body, view, logger)

@app.view("jira_3")
def jira_3(ack, body, view, logger):
    return slack_views.jira_3(ack, body, view, logger)

@app.view("user_emoji")
def user_emoji(ack, body, view, logger):
    return slack_views.user_emoji(ack, body, view, logger)

@app.view("select-time")
def select_time_view(ack, body, view, logger):
    return slack_views.select_time_view(ack, body, view, logger)

#events
@app.event("message")
def message(payload):
    return slack_events.message(payload)

@app.event("reaction_added")
def reaction_added(payload):
    return slack_events.reaction_added(payload)

@app.event("app_home_opened")
def app_home_opened(payload):
    return slack_events.app_home_opened(payload)

@app.event("app_uninstalled")
def app_uninstalled(payload):
    return slack_events.app_uninstalled(payload)

#commands
@app.command("/info")
def info(ack, command):
    return slack_commands.info(ack, command)

@app.command("/commands")
def commands(ack, command):
    return slack_commands.commands(ack, command)

@app.command("/unread-issues")
def unread_issues(ack, command):
    return slack_commands.unread_issues(ack, command)

@app.command("/update-issues")
def update_issues(ack, command):
    return slack_commands.update_issues(ack, command)

@app.command("/daily-stats")
def daily_stats(ack, command):
    return slack_commands.daily_stats(ack, command)

@app.command("/select-time")
def select_time_command(ack, command):
    return slack_commands.select_time_command(ack, command)

#actions
@app.action("static_select-rating")
def static_select_rating(ack, body, logger):
    return slack_actions.static_select_rating(ack, body, logger)

@app.action("select-time")
def select_time_action(ack, body, logger):
    return select_time_action(ack, body, logger)

@app.action("static_select-action")
def static_select_action(ack, body, logger):
    ack()
    print("static_select_action")
    return

@app.action("multi_conversations_select-action")
def multi_conversations_select_action(ack, body, logger):
    ack()
    print("multi_conversations_select_action")
    return

@app.action("multi_users_select-action")
def multi_users_select_action(ack, body, logger):
    ack()
    print("multi_users_select_action")
    return

@app.message("message")
def test_message(message):
    logging.error("Got a message")
    return


if __name__ == "__main__":
    from my_functions import long_thread
    long_thread.start()
    #app.start(port=int(os.environ.get("PORT", 8000)))
    handler = SocketModeHandler(app, APP_TOKEN)
    handler.start()