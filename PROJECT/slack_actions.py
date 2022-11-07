from slack_client import get_client
from my_db import db, update_db
import custom_messages
from datetime import datetime


#получить оценку пользователя об удовлетворенностью работой над тикетом Jira
def static_select_rating(ack, body, logger):
    ack() #подтвердить, что запрос был получен от Slack
    today = str(datetime.today().date())


    rating = int(body["actions"][0]["selected_option"]["text"]["text"])
    myquery = db.get_db()["rating"].find_one()
    if myquery:
        day = myquery["day"]
        if day == today:
            rating += myquery["rating"]
            people = myquery["people"] + 1
            newvalues = { "$set": {"day": day, "rating": rating, "people": people} }
            return db.get_db()["rating"].update_one(myquery, newvalues) #обновляем базу данных
    return update_db("rating", {"day": today, "rating": rating, "people": 1}, False) #создаем базу данных, если она была пустая или наступил следующий день


#кнопка для выбора промежутка времени, после которого тикеты будут требовать обновления
def select_time_action(ack, body, logger):
    ack() #подтвердить, что запрос был получен от Slack
    trigger_id = body["trigger_id"]
    return get_client().views_open(trigger_id=trigger_id, view=custom_messages.select_time_view) #запускается view для выбора промежутка времени