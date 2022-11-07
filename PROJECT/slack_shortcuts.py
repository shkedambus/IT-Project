from my_db import db
from slack_client import get_client
import custom_messages
import my_functions


#шорткат для подключения Jira к боту
def connect_jira(ack, payload):
    ack() #подтвердить, что запрос был получен от Slack
    user_id = payload["user"]["id"]
    trigger_id=payload["trigger_id"]
    if get_client().users_info(user=user_id)["user"]["is_admin"]:
        get_client().views_open(
            trigger_id=trigger_id,
            view=custom_messages.connect_jira_shortcut_1)
    else:
        return get_client().views_open(trigger_id=trigger_id, view=custom_messages.show_result(text=":warning: Only an administrators can use this command"))


#шорткат для раздачи прав на изменение статуса тикета Jira выбранным пользователям
def sup_users(ack, payload):
    ack() #подтвердить, что запрос был получен от Slack
    user_id = payload["user"]["id"]
    trigger_id = payload["trigger_id"]
    if my_functions.jira_connected():
        if get_client().users_info(user=user_id)["user"]["is_admin"]:
            return get_client().views_open(
                    trigger_id=trigger_id,
                    view=custom_messages.connect_jira_shortcut_3) #запускает view для третьего этапа подключения Jira к боту (все прошло успешно)
        else:
            return get_client().views_open(trigger_id=trigger_id, view=custom_messages.show_result(text=":warning: Only an administrators can use this command")) #пользователь, вызвавший шорткат, не обладает правами администратора
    else:
        return get_client().views_open(
                    trigger_id=trigger_id,
                    view=custom_messages.show_result(text=':warning: You need to connect Jira first. You can do it by using "Connect Jira" shortcut')) #Jira еще не подключена


#шорткат для выбора своих эмодзи для статусов тикета Jira
def select_emojis(ack, payload):
    ack() #подтвердить, что запрос был получен от Slack
    user_id = payload["user"]["id"]
    trigger_id = payload["trigger_id"]
    if my_functions.jira_connected():
        if my_functions.check_permission(user_id): #проверка пользователя на обладание правами
            statuses = db.get_db()["statuses"].find({"value": 1}).distinct("status")
            return get_client().views_open(
                        trigger_id=trigger_id,
                        view=custom_messages.select_emoji_shortcut(statuses)) #запускается view для выбора эмодзи для статусов тикета Jira
        else:
            return get_client().views_open(trigger_id=trigger_id, view=custom_messages.show_result(text=":warning: You don't have permission to manage Jira emoji reactions.")) #пользователь не обладает правами по изменению статуса тикета Jira
    else:
        return get_client().views_open(trigger_id=trigger_id, view=custom_messages.show_result(text=':warning: You need to connect Jira first. You can do it by using "Connect Jira" shortcut')) #Jira еще не подключена