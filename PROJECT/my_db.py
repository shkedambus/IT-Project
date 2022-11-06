from datetime import datetime
from pymongo import MongoClient
from slack_client import get_client

class MyDB:
    db = None
    cluster = None

    def get_cluster(self):
        if self.cluster:
            return self.cluster

        CONNECTION_STRING = "mongodb+srv://shkedambus:foFtyWYD41DZrZT0@ivr.zbasqqs.mongodb.net/?retryWrites=true&w=majority"
        self.cluster = MongoClient(CONNECTION_STRING)
        return self.cluster

    def get_db(self):
        if self.db:
            return self.db
        
        team_id = get_client().api_call("auth.test")["team_id"]
        self.db = self.get_cluster()[team_id]
        return self.db


db = MyDB()

#достать данные из бд и посчитать среднее время до взятия тикета Jira в работу
def get_time_to_start():
    myquery = db.get_db()["time"].find_one()
    result = 0
    if myquery:
        today = str(datetime.today().date())
        if myquery["day"] == today:
            if myquery["tickets_started"]:
                result = round(myquery["time_to_start"] / myquery["tickets_started"])
    return result #возвращает среднее время до взятия тикета Jira в работу


#достать данные из бд и посчитать среднее время до закрытия тикета Jira
def get_time_to_finish():
    myquery = db.get_db()["time"].find_one()
    result = 0
    if myquery:
        today = str(datetime.today().date())
        if myquery["day"] == today:
            if myquery["tickets_finished"]:
                result = round(myquery["time_to_finish"] / myquery["tickets_finished"])
    return result #возвращает среднее время до закрытия тикета Jira


#достать данные из бд и посчитать среднюю оценку удовлетворенности пользователя работой над тикетом Jira
def get_rating():
    myquery = db.get_db()["rating"].find_one()
    result = 0
    if myquery:
        today = str(datetime.today().date())
        if myquery["day"] == today:
            if myquery["people"]:
                result = round(int(myquery["rating"]) / int(myquery["people"]), 2)
    return result #возвращает среднюю оценку удовлетворенности пользователя работой над тикетом Jira


#обновить базу данных
def update_db(collection_name, data, many):
    collection = db.get_db()[collection_name]
    myquery = collection.find_one()
    if myquery:
        collection.drop()
        collection = db[collection_name]
        if many:
            collection.insert_many(data)
        else:
            collection.insert_one(data) 
    else:
        if many:
            collection.insert_many(data)
        else:
            collection.insert_one(data)