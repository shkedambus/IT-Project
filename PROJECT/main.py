import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import threading
from my_functions import send_daily_stats

from my_db import db
from slack_client import get_client

import slack_actions, slack_commands, slack_events, slack_shortcuts, slack_views
from config import Config


logging.basicConfig(level=logging.DEBUG)

config = Config()

BOT_TOKEN = config.get_bot_token()
SIGNING_SECRET = config.get_sign_secret()
APP_TOKEN = config.get_app_token()

logging.debug("tokens: ", BOT_TOKEN, SIGNING_SECRET, APP_TOKEN)

app = App(
    token=BOT_TOKEN,
    signing_secret=SIGNING_SECRET
)
client = get_client()




def form_user_collection():
    if "users" not in db.get_db().list_collection_names():
        support_team = []
        all_users = client.users_list()
        for member in all_users["members"]:
            if not member["is_bot"] and member["id"] != "USLACKBOT":
                support_team.append({"user": member["id"], "email": member["profile"]["email"], "notification": 24, "has_permission": False})
        db.get_db()["users"].insert_many(support_team)


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

    form_user_collection()

    long_thread = threading.Thread(target=send_daily_stats) #запуск ядра, которое будет ежедневно отправлять статистику по обработке тикетов Jira
    long_thread.start()
    #app.start(port=int(os.environ.get("PORT", 8000)))
    handler = SocketModeHandler(app, APP_TOKEN)
    handler.start()