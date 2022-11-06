import logging
import slack_sdk as slack
import os
# from pathlib import Path
# from dotenv import load_dotenv #чтобы забрать SLACK_TOKEN из env файла
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import datetime

from pymongo import MongoClient

#import custom_messages #файл с различными выводами бота

import threading
import time


# env_path = Path(".") / ".env" #указываем путь к env файлу
# load_dotenv(dotenv_path=env_path) #загружаем env файл

logging.basicConfig(level=logging.DEBUG)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logging.error("Bot token not found in env vars")
    exit(1)

SIGNING_SECRET = os.getenv("SIGNING_SECRET")
if not SIGNING_SECRET:
    logging.error("Signing secret not found in env vars")
    exit(1)

APP_TOKEN = os.getenv("APP_TOKEN")
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


#достать канал, в котором есть бот
def get_channel():
    channel_id = None
    for result in client.conversations_list():
        if channel_id is not None:
            break
        for channel in result["channels"]:
            if channel["is_member"]:
                channel_id = channel["id"]
                break
    return channel_id #возвращает id канала


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


##result = on_start()
#BOT_ID = result["bot_id"]
#JIRA_ID = result["jira_id"]


#найти id пользователя по его имени
def find_user_by_name(user_name):
    users = client.users_list()
    for user in users["members"]:
        if user["name"] == user_name:
            return user["id"] #возвращает id пользователя


#проверить, подключена ли Jira
def jira_connected():
    return "jira" in db.list_collection_names() #возвращает True, если Jira подключена, иначе - False


#обрезать сообщение пользователя для названия тикета в Jira
def cut_to_summary(text):
    hellos = ["привет", "здравствуй", "hey", "hi", "hello"] #список слов, которые нужно убрать (например: чтобы убрать "привет" в сообщении "привет! ничего не работает")
    text_list = text.split()
    new_text_list = []
    for word in text_list:
        for hello in hellos:
            if hello in word.lower():
                new_text_list.append(word)
                break
    for word in new_text_list:
        text_list.remove(word)


    how_many_words = 6
    summary = " ".join(text_list[:how_many_words])
    return summary #возвращает summary тикета Jira (название тикета)


#достать данные из бд и посчитать среднее время до взятия тикета Jira в работу
def get_time_to_start():
    myquery = db["time"].find_one()
    result = 0
    if myquery:
        today = str(datetime.datetime.today().date())
        if myquery["day"] == today:
            if myquery["tickets_started"]:
                result = round(myquery["time_to_start"] / myquery["tickets_started"])
    return result #возвращает среднее время до взятия тикета Jira в работу


#достать данные из бд и посчитать среднее время до закрытия тикета Jira
def get_time_to_finish():
    myquery = db["time"].find_one()
    result = 0
    if myquery:
        today = str(datetime.datetime.today().date())
        if myquery["day"] == today:
            if myquery["tickets_finished"]:
                result = round(myquery["time_to_finish"] / myquery["tickets_finished"])
    return result #возвращает среднее время до закрытия тикета Jira


#достать данные из бд и посчитать среднюю оценку удовлетворенности пользователя работой над тикетом Jira
def get_rating():
    myquery = db["rating"].find_one()
    result = 0
    if myquery:
        today = str(datetime.datetime.today().date())
        if myquery["day"] == today:
            if myquery["people"]:
                result = round(int(myquery["rating"]) / int(myquery["people"]), 2)
    return result #возвращает среднюю оценку удовлетворенности пользователя работой над тикетом Jira


#отправить статистику за день каждый день в 20:00
def send_daily_stats():
    send_time = datetime.datetime.strptime("20:00:00", "%H:%M:%S")
    while True:
        current_time = datetime.datetime.strptime(datetime.datetime.today().strftime("%H:%M:%S"), "%H:%M:%S")
        if current_time == send_time:
            channel_id = get_channel()
            import my_jira
            result = my_jira.get_daily_stats_tickets()
            time_to_start = get_time_to_start()
            time_to_finish = get_time_to_finish()
            rating = get_rating()
            client.chat_postMessage(channel=channel_id, 
                                    blocks=custom_messages.get_stats_blocks(created=str(result[0]), 
                                                                            in_progress=str(result[1]),
                                                                            done=str(result[2]), 
                                                                            unread=str(result[3]), 
                                                                            avg_to_start=str(time_to_start // 60), 
                                                                            avg_to_finish=str(time_to_finish // 60), 
                                                                            rating=str(rating)))
            # time.sleep(86399)
        else:
            time.sleep(abs((send_time - current_time).total_seconds()))
long_thread = threading.Thread(target=send_daily_stats) #запуск ядра, которое будет ежедневно отправлять статистику по обработке тикетов Jira


#обновить базу данных
def update_db(collection_name, data, many):
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


#проверить пользователя на право изменения тикета Jira
def check_permission(user_id):
    return db["users"].find_one({"user": user_id})["has_permission"] #возвращает True, если пользователь обладает правом на изменение тикета Jira, иначе - False


#расписать пользователю про реакции и соответствующии им статусы Jira
def user_reactions(user_id, select_emoji=False):
    blocks = custom_messages.emoji_and_their_statuses(select_emoji)
    client.chat_postMessage(channel=f"@{user_id}", blocks=blocks) #вывод сообщения (эмодзи - статус)


#проверить домена и api токен Jira
def check_connection(domain, api_token, user_email):
    import requests
    from requests.auth import HTTPBasicAuth
    url = "https://" + domain + ".atlassian.net/rest/api/3/project"
    auth = HTTPBasicAuth(user_email, api_token)
    headers = {
        "Accept": "application/json"
    }
    try:
        response = requests.request(
            "GET",
            url,
            headers=headers,
            auth=auth
        )
        if response.status_code == 404 or response.status_code == 401:
            return False
        else:
            return True
    except:
        return False


#уведомить пользователя об изменении статуса тикета Jira
def notify_reporter(reporter_id, assignee_id, issue_key, old_status, new_status):
    import my_jira
    issue_summary = my_jira.get_ticket_summary(issue_key)


    assignee_name = client.users_info(user=assignee_id)["user"]["name"]
    if assignee_id != reporter_id:
        return client.chat_postMessage(channel=f"@{reporter_id}", 
                                    blocks=custom_messages.get_notification_blocks(issue_key=issue_key, issue_summary=issue_summary, old_status=old_status, new_status=new_status, user_id=assignee_id, user_name=assignee_name))
        #отправляем пользователю, создавшему тикет Jira, уведомление об изменении его статуса (тикет [тикет] был изменен [пользователь], старый статус: [старый статус], новый статус: [новый статус])


#получить оценку пользователя об удовлетворенностью работой над тикетом Jira
@app.action("static_select-rating")
def static_select_rating(ack, body, logger):
    ack() #метод ack(), используемый в этом и во всех дальнейших прослушивателях действий, требуется для подтверждения того, что запрос был получен от Slack
    today = str(datetime.datetime.today().date())


    rating = int(body["actions"][0]["selected_option"]["text"]["text"])
    myquery = db["rating"].find_one()
    if myquery:
        day = myquery["day"]
        if day == today:
            rating += myquery["rating"]
            people = myquery["people"] + 1
            newvalues = { "$set": {"day": day, "rating": rating, "people": people} }
            return db["rating"].update_one(myquery, newvalues) #обновляем базу данных
    return update_db("rating", {"day": today, "rating": rating, "people": 1}, False) #создаем базу данных, если она была пустая или наступил следующий день


#шорткат для подключения Jira к боту
@app.shortcut("connect_jira")
def connect_jira(ack, payload):
    ack()
    user_id = payload["user"]["id"]
    trigger_id=payload["trigger_id"]
    if client.users_info(user=user_id)["user"]["is_admin"]:
        client.views_open(
            trigger_id=trigger_id,
            view=custom_messages.connect_jira_shortcut_1)
    else:
        return client.views_open(trigger_id=trigger_id, view=custom_messages.show_result(text=":warning: Only an administrators can use this command"))


#добавление стандартных реакций при подключении Jira к боту
def configure_reactions():
    import my_jira
    statuses = my_jira.miha_test_issue()
    # data = [
    #     { "emoji": "white_check_mark", "transition_id": statuses[-1]["transition_id"], "transition_name": statuses[-1]["transition_name"], "transition_value": statuses[-1]["transition_value"]},
    #     { "emoji": "eyes", "transition_id": statuses[1]["transition_id"], "transition_name": statuses[1]["transition_name"], "transition_value": statuses[1]["transition_value"]},
    #     { "emoji": "exclamation", "transition_id": statuses[0]["transition_id"], "transition_name": statuses[0]["transition_name"], "transition_value": statuses[0]["transition_value"]}
    # ]
    emoji_dict = {"1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine"}
    data = [{"emoji": "exclamation", "transition_id": statuses[0]["transition_id"], "transition_name": statuses[0]["transition_name"], "transition_value": statuses[0]["transition_value"]}]
    for i in range(1, len(statuses) - 1):
        data.append({"emoji": emoji_dict[str(i)], "transition_id": statuses[i]["transition_id"], "transition_name": statuses[i]["transition_name"], "transition_value": statuses[i]["transition_value"]})
    data.append({"emoji": "white_check_mark", "transition_id": statuses[-1]["transition_id"], "transition_name": statuses[-1]["transition_name"], "transition_value": statuses[-1]["transition_value"]})
    status_data = {
        "value": 1,
        "status": statuses
    }
    update_db("reactions", data, True) #создаем коллекцию reactions (эмодзи - статус)
    update_db("statuses", status_data, False) #создаем коллекцию statuses (id статуса, название статуса, значение статуса)


#view для первого этапа подключения Jira к боту (ввод доменного имя и api ключа Jira)
@app.view("jira_1")
def jira_1(ack, body, view, logger):
    trigger_id = body["trigger_id"]
    user_id = body["user"]["id"]
    user_email = client.users_info(user=user_id)["user"]["profile"]["email"]
    domain = view["state"]["values"]["domain"]["domain"]["value"]
    api_token = view["state"]["values"]["api"]["api"]["value"]
    ack()
    if check_connection(domain=domain, api_token=api_token, user_email=user_email):
        import my_jira
        projects = my_jira.get_all_projects(domain=domain, api_token=api_token, user_email=user_email)
        db["temp"].insert_one({"domain": domain, "api_key": api_token, "email": user_email})
        return client.views_open(trigger_id=trigger_id, view=custom_messages.connect_jira_shortcut_2(projects)) #запускает view для второго этапа подключения Jira к боту
    else:
        return client.views_open(trigger_id=trigger_id, view=custom_messages.show_result(text=":warning: Wrong Jira domain name or API token.")) #показывает ошибку, если доменное имя или api токен недействительны


#view для второго этапа подключения Jira к боту (выбор проекта Jira и канала для обработки обращений)
@app.view("jira_2")
def jira_2(ack, body, view, logger):
    ack()
    trigger_id = body["trigger_id"]
    user_id = body["user"]["id"]
    selected_project = view["state"]["values"]["static-select-action"]["static_select-action"]["selected_option"]["value"]
    myquery = db["temp"].find_one()
    domain = myquery["domain"]
    api_key = myquery["api_key"]
    email = myquery["email"]
    db["temp"].drop()
    update_db("jira", {"domain": domain, "api_key": api_key, "email": email, "project": selected_project}, False)


    client.chat_postMessage(channel=f"@{user_id}", text="Jira has been successfully connected!")
    client.views_open(trigger_id=trigger_id, view=custom_messages.connect_jira_shortcut_3)


    selected_channels = view["state"]["values"]["multi_conversations_select-action"]["multi_conversations_select-action"]["selected_conversations"]
    print(selected_channels)
    for selected_channel in selected_channels:
        try:
            is_im = client.conversations_info(channel=str(selected_channel))["channel"]["is_im"]
            if not is_im:
                client.conversations_join(channel=selected_channel) #бот заходит в выбранный пользователем канал для обработки сообщений
                client.chat_postMessage(channel=selected_channel, blocks=custom_messages.onboarding_blocks) #бот отправляет сообщение, что Jira была успешно подключена
        except:
            print("")


#шорткат для раздачи прав на изменение статуса тикета Jira выбранным пользователям
@app.shortcut("sup_users")
def sup_users(ack, payload):
    ack()
    user_id = payload["user"]["id"]
    trigger_id = payload["trigger_id"]
    if jira_connected():
        if client.users_info(user=user_id)["user"]["is_admin"]:
            return client.views_open(
                    trigger_id=trigger_id,
                    view=custom_messages.connect_jira_shortcut_3) #запускает view для третьего этапа подключения Jira к боту (все прошло успешно)
        else:
            return client.views_open(trigger_id=trigger_id, view=custom_messages.show_result(text=":warning: Only an administrators can use this command")) #пользователь, вызвавший шорткат, не обладает правами администратора
    else:
        return client.views_open(
                    trigger_id=trigger_id,
                    view=custom_messages.show_result(text=':warning: You need to connect Jira first. You can do it by using "Connect Jira" shortcut')) #Jira еще не подключена


#view для третьего этапа подключения Jira к боту (выбор пользователей, которые могут изменять статус тикета Jira)
@app.view("jira_3")
def jira_3(ack, body, view, logger):
    ack()
    # trigger_id = body["trigger_id"]
    # user_id = body["user"]["id"]


    configure_reactions()
    selected_users = view["state"]["values"]["multi_users_select-action"]["multi_users_select-action"]["selected_users"] #список выбранных пользователей
    all_users = client.users_list()["members"] #список всех пользователей
    newvalues = []
    for object in all_users:
        user = object["id"]
        myquery = db["users"].find_one({"user": user})
        if user in selected_users:
            #выдача прав пользователям, которые были выбраны
            if not client.users_info(user=user)["user"]["is_bot"] and not user == "USLACKBOT":  #если пользователь не бот

                
                email = myquery["email"]
                notification = myquery["notification"]
                newvalues.append({"user": user, "email": email, "notification": notification, "has_permission": True})
                user_reactions(user)
        else:
            #обнуление прав пользователям, которые не были выбраны
            if not client.users_info(user=user)["user"]["is_bot"] and not user == "USLACKBOT": #если пользователь не бот

                
                email = myquery["email"]
                notification = myquery["notification"]
                newvalues.append({"user": user, "email": email, "notification": notification, "has_permission": False})
    return update_db("users", newvalues, True) #обновление базы данных


#шорткат для выбора своих эмодзи для статусов тикета Jira
@app.shortcut("select_emojis")
def select_emojis(ack, payload):
    ack()
    user_id = payload["user"]["id"]
    trigger_id = payload["trigger_id"]
    if jira_connected():
        if check_permission(user_id): #проверка пользователя на обладание правами
            statuses = db["statuses"].find({"value": 1}).distinct("status")
            return client.views_open(
                        trigger_id=trigger_id,
                        view=custom_messages.select_emoji_shortcut(statuses)) #запускается view для выбора эмодзи для статусов тикета Jira
        else:
            return client.views_open(trigger_id=trigger_id, view=custom_messages.show_result(text=":warning: You don't have permission to manage Jira emoji reactions.")) #пользователь не обладает правами по изменению статуса тикета Jira
    else:
        return client.views_open(trigger_id=trigger_id, view=custom_messages.show_result(text=':warning: You need to connect Jira first. You can do it by using "Connect Jira" shortcut')) #Jira еще не подключена


#view для получения эмодзи пользователя
@app.view("user_emoji")
def user_emoji(ack, body, view, logger):
    ack()
    # user_id = body["user"]["id"]
    trigger_id = body["trigger_id"]
    from slack_emojis import get_emoji #берем список всех эмодзи Slack из файла slack_emojis.py
    custom_emojis = list(client.emoji_list()["emoji"].keys()) #берем список всех пользовательских эмодзи Slack
    all_emojis = get_emoji()
    all_emojis.extend(custom_emojis) #соединяем два списка в один
    data = [] #сбор новых данных для обновления базы данных
    selected_emojis = [] #список для проверки (был ли эмодзи уже выбран пользователем ранее)
    for key in list(view["state"]["values"].keys()): #для каждого выбранного пользователем статуса
        transition = key.split("|")
        transition_id = transition[0]
        transition_name = transition[1]
        transition_value = transition[2]
        emoji = view["state"]["values"][key][transition_id]["value"]
        if emoji in all_emojis:
            if emoji not in selected_emojis:
                newvalues = { "emoji": emoji, "transition_id": transition_id, "transition_name": transition_name, "transition_value": transition_value}
                data.append(newvalues)
                selected_emojis.append(emoji)
            else:
                return client.views_open(trigger_id=trigger_id, view=custom_messages.show_result(text=":warning: Invalid input\nTrying to apply identical emoji to different Jira statuses")) #вывод сообщения об ошибке (один и тот же эмодзи для нескольких статусов)
        else:
            return client.views_open(trigger_id=trigger_id, view=custom_messages.show_result(text=f':warning: Invalid input\nEmoji "{emoji}" does not exist')) #вывод сообщения об ошибке (недействительный эмодзи)
    update_db("reactions", data, True)
    client.views_open(trigger_id=trigger_id, view=custom_messages.show_result(text="All changes have been successfully applied!")) #вывод сообщения, что все изменения были успешно применены
    users = db["users"].find({"has_permission": True}).distinct("user")
    for user in users: #уведомление каждого пользователя, обладающего правами по изменению статуса тикета Jira, об изменении эмодзи для статусов тикетов Jira
        user_reactions(user, True) 
            

#ивент - отправлено сообщение
@app.event("message")
def message(payload):
    if "subtype" not in payload.keys() and jira_connected(): #если Jira подключена
        import my_jira
        #получение данных о сообщении (канал, пользователь, содержание, время)
        channel_id = payload["channel"]
        is_im = client.conversations_info(channel=channel_id)["channel"]["is_im"]
        user_id = payload["user"]
        text = payload["text"]
        ts = payload["ts"]


        if user_id != BOT_ID and user_id != None and user_id != JIRA_ID and user_id != "USLACKBOT" and not is_im: #если сообщение было отправлено в общий канал не ботом и не Jira
            issue_summary = cut_to_summary(text) #формирование названия тикета
            user_name = client.users_info(user=user_id)["user"]["name"] #получение имени пользователя, создавшего тикет
            description = user_name + ": " + text #формирование описания тикета
            my_jira.create_ticket(summary=issue_summary, description=description) #создание тикета


            #получение данных из созданного тикета для формирования сообщения о создании этого тикета
            issue_key = str(my_jira.search_ticket(summary=issue_summary))
            assignee = my_jira.get_ticket_assignee(issue_key)
            if assignee == "None":
                assignee = "Unassigned"
            current_status = str(my_jira.get_ticket_status(key=issue_key, field="name"))


            return client.chat_postMessage(channel=channel_id, thread_ts=ts,
                                        blocks=custom_messages.get_created_ticket_blocks(issue_key=issue_key, issue_summary=issue_summary, reporter_id=user_id, reporter_name=user_name, assignee=assignee, current_status=current_status))
            #вывод сообщения о создании тикета


#ивент - добавлена реакция на сообщение
@app.event("reaction_added")
def reaction_added(payload):
    #получение данных о реакции (автор сообщения, отреагировавший пользователь, канал, время, реакция)
    message_user_id = payload["item_user"]
    reaction_user_id = payload["user"]
    channel_id = payload["item"]["channel"]
    is_im = client.conversations_info(channel=channel_id)["channel"]["is_im"]
    ts = payload["item"]["ts"]
    reaction = payload["reaction"]  


    try:
        #получаем сообщение, на которое поставили реакцию
        message = client.conversations_history(
            channel=channel_id,
            inclusive=True,
            oldest=ts,
            limit=1)["messages"][0]


        collection_reactions = db["reactions"]
        if jira_connected() and check_permission(reaction_user_id) and collection_reactions.find({"emoji": reaction}): #если Jira подключена, пользователь обладает правами по изменению статуса тикета Jira и его реакция соответствует какому-либо статусу тикета Jira
            import my_jira
            #если это сообщение самого пользователя в канале
            if message_user_id != BOT_ID and not is_im:
                issue_summary = cut_to_summary(message["text"])
                issue_key = str(my_jira.search_ticket(issue_summary))
                reporter_id=message_user_id
            #если это сообщение бота в личных сообщениях
            elif message_user_id == BOT_ID and is_im:
                issue_key = message["blocks"][0]["block_id"]
                reporter_name = message["blocks"][0]["text"]["text"].split("|")[1].split()[1][:-1]
                reporter_id = find_user_by_name(reporter_name)
            #если это что-то другое, то пустые значения ключа тикета и создателя тикета вызовут ошибку
            else:
                issue_key = None
                reporter_id = None


            ticket_was_unread = my_jira.if_ticket_unread(issue_key) #проверка: изменен ли был когда-либо до этого тикет
            #поля для сбора статистики (время до взятия тикета в работу, время до закрытия тикета, сколько тикетов начато, сколько тикетов закрыто)
            time_to_start = 0
            time_to_finish = 0
            tickets_started = 0
            tickets_finished = 0


            transition_id = collection_reactions.find({"emoji": reaction}).distinct("transition_id")[0]
            transition_value = collection_reactions.find({"emoji": reaction}).distinct("transition_value")[0]


            current_status = my_jira.get_ticket_status(issue_key) #получение текущего статуса тикета
            if current_status != str(transition_id): #если тикету был присвоен новый статус
                user = client.users_info(user=reaction_user_id)["user"]["profile"]["email"]

                
                old_status = my_jira.get_ticket_status(key=issue_key, field="name")
                my_jira.change_status(issue_key, transition_id, user) #изменение статуса тикета
                new_status = my_jira.get_ticket_status(key=issue_key, field="name")
                notify_reporter(reporter_id=reporter_id, assignee_id=reaction_user_id, issue_key=issue_key, old_status=old_status, new_status=new_status) #уведомление пользователя, создавшего тикет, об изменении статуса этого тикета


                if str(transition_value) == "done": #если тикет теперь закрыт
                    time_to_finish = my_jira.get_ticket_time(issue_key)
                    tickets_finished = 1
                    text = "Task " + issue_key + " was done." 
                    client.chat_postMessage(channel=f"@{reporter_id}", blocks=custom_messages.get_rating_blocks(text)) #отправка сообщения, в котором запрашивается оценка, пользователю, создавшему тикет


                if ticket_was_unread: #если тикет не был изменен до этого момента, происходит сбор статистики
                    time_to_start = my_jira.get_ticket_time(issue_key)
                    tickets_started = 1


                #обновление статистики в базе данных
                today = str(datetime.datetime.today().date())
                myquery = db["time"].find_one()
                if myquery:
                    day = myquery["day"]
                    if day == today: #проверка на дату, так как статистика обнуляется с каждым новым днем
                        time_to_start += myquery["time_to_start"]
                        tickets_started += myquery["tickets_started"]
                        time_to_finish += myquery["time_to_finish"]
                        tickets_finished += myquery["tickets_finished"]
                        newvalues = { "$set": {"day": today, "time_to_start": time_to_start, "tickets_started": tickets_started, "time_to_finish": time_to_finish, "tickets_finished": tickets_finished} }
                        db["time"].update_one(myquery, newvalues)
                    else:
                        db["time"].update_one(myquery, { "$set": {"day": today, "time_to_start": time_to_start, "tickets_started": tickets_started, "time_to_finish": time_to_finish, "tickets_finished": tickets_finished} })
                else:
                    db["time"].insert_one({"day": today, "time_to_start": time_to_start, "tickets_started": tickets_started, "time_to_finish": time_to_finish, "tickets_finished": tickets_finished})
    except:
        print("User reacted to wrong message or some error occurred") #пустые значения ключа тикета и создателя тикета вызвали ошибку


#ивент - открыта вкладка home
@app.event("app_home_opened")
def app_home_opened(payload):
    user_id = payload["user"]
    update_blocks = []
    if check_permission(user_id): #если пользователь обладает правами на изменения статуса тикета Jira
        import my_jira
        user_email = client.users_info(user=user_id)["user"]["profile"]["email"]
        result_dict = my_jira.get_unupdated_tickets(user_id, user_email) #получение тикетов, требующих обновления
        if result_dict:
            #формирование блоков для вывода бота
            update_blocks.append({
                                    "type": "section",
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": ":eyes: Following Jira issues need to be updated:"
                                    }
                                })
            for issue_key, value in result_dict.items():
                reporter_name = value[1].split()[0]
                issue_summary = reporter_name + " " + value[0]
                update_blocks.extend(custom_messages.get_unread_ticket_blocks(issue_key=issue_key, issue_summary=issue_summary))
        else:
            update_blocks.append({
                                    "type": "section",
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": ":heavy_check_mark: All Jira issues are updated."
                                    }
                                })


    return client.views_publish(user_id=user_id, view=custom_messages.get_app_home_view(update_blocks)) #вывод полученной информации на вкладке


#ивент - бот был удален пользователем
@app.event("app_uninstalled")
def app_uninstalled(payload):
    return cluster.drop_database(TEAM_ID) #удаление базы данных для этого рабочего пространства


#комманда /info для вывода информации о пользователях, проекте Jira, реакциях и соответствующих статусах
@app.command("/info")
def info(ack, command):
    ack()
    user_id = command["user_id"]
    if jira_connected(): #если Jira подключена
        myquery = db["jira"].find_one()
        domain = myquery["domain"]
        project = myquery["project"]
        url = "https://" + domain + ".atlassian.net"
        
        #получение информации о пользователях, обладающих правом на изменения статуса тикета Jira и формирование блоков для вывода бота
        user_ids = db["users"].find({"has_permission": True}).distinct("user")
        users = []
        if user_ids:   
            for user_id in user_ids:
                users.append([user_id, client.users_info(user=user_id)["user"]["name"]])
        blocks = custom_messages.get_info_blocks(url = url, project=project, users=users, user_id=user_id)
    else:
        blocks = custom_messages.jira_not_connected
    return client.chat_postMessage(channel=f"@{user_id}", blocks=blocks)


#комманда /commands для вывода всех существующих комманд бота
@app.command("/commands")
def commands(ack, command):
    ack()
    user_id = command["user_id"]
    return client.chat_postMessage(channel=f"@{user_id}", blocks=custom_messages.commands_blocks)


#комманда /unread-issues для получения непрочитанных тикетов
@app.command("/unread-issues")
def unread_issues(ack, command):
    ack()
    user_id = command["user_id"]
    if jira_connected(): #если Jira подключена
        import my_jira
        result_dict = my_jira.get_unread_tickets() #получение всех непрочитанных тикетов
        if result_dict: #если есть непрочитанные тикеты
            client.chat_postMessage(channel=f"@{user_id}", text=":eyes: Following Jira issues are unread:")
            for issue_key, value in result_dict.items():
                reporter_name = value[1].split()[0]
                issue_summary = reporter_name + " " + value[0]
                client.chat_postMessage(channel=f"@{user_id}", blocks=custom_messages.get_unread_ticket_blocks(issue_key=issue_key, issue_summary=issue_summary)) #вывод всех непрочитанных тикетов
        else:
            client.chat_postMessage(channel=f"@{user_id}", text=":heavy_check_mark: No unread Jira issues.") #непрочитанных тикетов нет
    else:
        client.chat_postMessage(channel=f"@{user_id}", blocks=custom_messages.jira_not_connected) #Jira не подключена


#комманда /update-issues для получения тикетов, требующих обновления
@app.command("/update-issues")
def update_issues(ack, command):
    ack()
    user_id = command["user_id"]
    if jira_connected(): #если Jira подключена
        import my_jira
        user_email = client.users_info(user=user_id)["user"]["profile"]["email"]
        result_dict = my_jira.get_unupdated_tickets(user_id, user_email) #получение всех тикетов, требующих обновления
        if result_dict: #если есть тикеты, требующие обновления
            client.chat_postMessage(channel=f"@{user_id}", text=":eyes: Following Jira issues need to be updated:")
            for issue_key, value in result_dict.items():
                reporter_name = value[1].split()[0]
                issue_summary = reporter_name + " " + value[0]
                client.chat_postMessage(channel=f"@{user_id}", blocks=custom_messages.get_unread_ticket_blocks(issue_key=issue_key, issue_summary=issue_summary))
        else:
            client.chat_postMessage(channel=f"@{user_id}", text=":heavy_check_mark: All Jira issues are updated.") #тикетов, требующих обновления, нет
    else:
        client.chat_postMessage(channel=f"@{user_id}", blocks=custom_messages.jira_not_connected) #Jira не подключена


#комманда /daily-stats для получения ежедневной статистики по обработанным обращениям
@app.command("/daily-stats")
def daily_stats(ack, command):
    ack()
    user_id = command["user_id"]
    if jira_connected(): #если Jira подключена
        import my_jira
        #получение статистики
        result = my_jira.get_daily_stats_tickets()
        time_to_start = get_time_to_start()
        time_to_finish = get_time_to_finish()
        rating = get_rating()
        #вывод статистики
        return client.chat_postMessage(channel=f"@{user_id}", blocks=custom_messages.get_stats_blocks(created=str(result[0]), in_progress=str(result[1]), done=str(result[2]), unread=str(result[3]), avg_to_start=str(time_to_start // 60), avg_to_finish=str(time_to_finish // 60), rating=str(rating)))
    else:
        return client.chat_postMessage(channel=f"@{user_id}", blocks=custom_messages.jira_not_connected) #Jira не подключена


#комманда /select-time для выбора промежутка времени, после которого тикеты будут требовать обновления
@app.command("/select-time")
def select_time_command(ack, command):
    ack()
    trigger_id = command["trigger_id"]
    # user_id = command["user_id"]
    return client.views_open(trigger_id=trigger_id, view=custom_messages.select_time_view) #запускается view для выбора промежутка времени


#кнопка для выбора промежутка времени, после которого тикеты будут требовать обновления
@app.action("select-time")
def select_time_action(ack, body, logger):
    ack()
    trigger_id = body["trigger_id"]
    return client.views_open(trigger_id=trigger_id, view=custom_messages.select_time_view) #запускается view для выбора промежутка времени


#view для выбора промежутка времени
@app.view("select-time")
def select_time_view(ack, body, view, logger):
    ack()
    user_id = body["user"]["id"]
    trigger_id = body["trigger_id"]
    try:
        #получение данных о пользователе и выбранном промежутке времени
        hours = int(view["state"]["values"]["select-time"]["select-time"]["value"])
        myquery = db["users"].find_one({"user": user_id})
        email = myquery["email"]
        has_permission = myquery["has_permission"]
        newvalues = { "$set": {"user": user_id, "email": email, "notification": hours, "has_permission": has_permission} }
        db["users"].update_one(myquery, newvalues) #обновление базы данных
        return client.views_open(trigger_id=trigger_id, view=custom_messages.show_result(text="All changes have been successfully applied!")) #все изменения были успешно применены
    except:
        return client.views_open(trigger_id=trigger_id, view=custom_messages.show_result(text=":warning: Invalid input.")) #пользователь ввел недействительные данные


#блоки, чтобы лишние предупреждения при использовании кнопок не мелькали перед глазами:

@app.action("static_select-action")
def static_select_action(ack, body, logger):
    ack()
    return


@app.action("multi_conversations_select-action")
def multi_conversations_select_action(ack, body, logger):
    ack()
    return


@app.action("multi_users_select-action")
def multi_users_select_action(ack, body, logger):
    ack()
    return


@app.message("message")
def test_message(message):
    logging.error("Got a message")
    return

if __name__ == "__main__":
    long_thread.start()
    #app.start(port=int(os.environ.get("PORT", 8000)))
    handler = SocketModeHandler(app, APP_TOKEN)
    handler.start()
