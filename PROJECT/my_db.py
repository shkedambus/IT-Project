from datetime import datetime


#достать данные из бд и посчитать среднее время до взятия тикета Jira в работу
def get_time_to_start():
    from main import db
    myquery = db["time"].find_one()
    result = 0
    if myquery:
        today = str(datetime.today().date())
        if myquery["day"] == today:
            if myquery["tickets_started"]:
                result = round(myquery["time_to_start"] / myquery["tickets_started"])
    return result #возвращает среднее время до взятия тикета Jira в работу


#достать данные из бд и посчитать среднее время до закрытия тикета Jira
def get_time_to_finish():
    from main import db
    myquery = db["time"].find_one()
    result = 0
    if myquery:
        today = str(datetime.today().date())
        if myquery["day"] == today:
            if myquery["tickets_finished"]:
                result = round(myquery["time_to_finish"] / myquery["tickets_finished"])
    return result #возвращает среднее время до закрытия тикета Jira


#достать данные из бд и посчитать среднюю оценку удовлетворенности пользователя работой над тикетом Jira
def get_rating():
    from main import db
    myquery = db["rating"].find_one()
    result = 0
    if myquery:
        today = str(datetime.today().date())
        if myquery["day"] == today:
            if myquery["people"]:
                result = round(int(myquery["rating"]) / int(myquery["people"]), 2)
    return result #возвращает среднюю оценку удовлетворенности пользователя работой над тикетом Jira


#обновить базу данных
def update_db(collection_name, data, many):
    from main import db
    collection = db[collection_name]
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