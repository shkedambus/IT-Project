from slack_client import get_client, get_bot_id
import custom_messages
import my_functions
from datetime import datetime
from my_db import db


#получаем id бота и Jira
def get_bot_jira_id():
    if "id" not in db.get_db().list_collection_names():
        bot_id = get_bot_id()
        jira_id = ""
        all_users = get_client().users_list()
        for member in all_users["members"]:
            if member["is_bot"] and member["real_name"] == "Jira":
                jira_id = member["id"]
        db.get_db()["id"].insert_one({"bot_id": bot_id, "jira_id": jira_id})
    else:
        myquery = db.get_db()["id"].find_one()
        bot_id = myquery["bot_id"]
        jira_id = myquery["jira_id"]

    return {"bot_id": bot_id, "jira_id": jira_id} #возвращает словарь, содержащий id бота и id Jira (если есть)

#ивент - отправлено сообщение
def message(payload):
    if "subtype" not in payload.keys() and my_functions.jira_connected(): #если Jira подключена
        import my_jira
        #получение данных о сообщении (канал, пользователь, содержание, время)
        channel_id = payload["channel"]
        is_im = get_client().conversations_info(channel=channel_id)["channel"]["is_im"]
        user_id = payload["user"]
        text = payload["text"]
        ts = payload["ts"]

        result = get_bot_jira_id()
        bot_id = result["bot_id"]
        jira_id = result["jira_id"]
        if user_id != bot_id and user_id != None and user_id != jira_id and user_id != "USLACKBOT" and not is_im: #если сообщение было отправлено в общий канал не ботом и не Jira
            issue_summary = my_functions.cut_to_summary(text) #формирование названия тикета
            user_name = get_client().users_info(user=user_id)["user"]["name"] #получение имени пользователя, создавшего тикет
            description = user_name + ": " + text #формирование описания тикета

            summaries = my_jira.get_all_summaries()
            #проверка на существование тикета с таким же названием
            if issue_summary not in summaries: 
                my_jira.create_ticket(summary=issue_summary, description=description) #создание тикета


                #получение данных из созданного тикета для формирования сообщения о создании этого тикета
                issue_key = str(my_jira.search_ticket(summary=issue_summary))
                assignee = my_jira.get_ticket_assignee(issue_key)
                if assignee == "None":
                    assignee = "Unassigned"
                current_status = str(my_jira.get_ticket_status(key=issue_key, field="name"))


                #вывод сообщения о создании тикета
                return get_client().chat_postMessage(channel=channel_id, thread_ts=ts,
                                                blocks=custom_messages.get_created_ticket_blocks(issue_key=issue_key, issue_summary=issue_summary, reporter_id=user_id, reporter_name=user_name, assignee=assignee, current_status=current_status))
            else:
                #тикет уже существует
                return get_client().chat_postMessage(channel=f"@{user_id}", text="Such Jira issue already exists")


#ивент - добавлена реакция на сообщение
def reaction_added(payload):
    #получение данных о реакции (автор сообщения, отреагировавший пользователь, канал, время, реакция)
    message_user_id = payload["item_user"]
    reaction_user_id = payload["user"]
    channel_id = payload["item"]["channel"]
    is_im = get_client().conversations_info(channel=channel_id)["channel"]["is_im"]
    ts = payload["item"]["ts"]
    reaction = payload["reaction"]  


    try:
        #получаем сообщение, на которое поставили реакцию
        message = get_client().conversations_history(
            channel=channel_id,
            inclusive=True,
            oldest=ts,
            limit=1)["messages"][0]


        collection_reactions = db["reactions"]
        if my_functions.jira_connected() and my_functions.check_permission(reaction_user_id) and collection_reactions.find({"emoji": reaction}): #если Jira подключена, пользователь обладает правами по изменению статуса тикета Jira и его реакция соответствует какому-либо статусу тикета Jira
            import my_jira
            #если это сообщение самого пользователя в канале
            bot_id = get_bot_id()
            if message_user_id != bot_id and not is_im:
                issue_summary = my_functions.cut_to_summary(message["text"])
                issue_key = str(my_jira.search_ticket(issue_summary))
                reporter_id=message_user_id
            #если это сообщение бота в личных сообщениях
            elif message_user_id == bot_id and is_im:
                issue_key = message["blocks"][0]["block_id"]
                reporter_name = message["blocks"][0]["text"]["text"].split("|")[1].split()[1][:-1]
                reporter_id = my_functions.find_user_by_name(reporter_name)
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
                user = get_client().users_info(user=reaction_user_id)["user"]["profile"]["email"]

                
                old_status = my_jira.get_ticket_status(key=issue_key, field="name")
                my_jira.change_status(issue_key, transition_id, user) #изменение статуса тикета
                new_status = my_jira.get_ticket_status(key=issue_key, field="name")
                my_functions.notify_reporter(reporter_id=reporter_id, assignee_id=reaction_user_id, issue_key=issue_key, old_status=old_status, new_status=new_status) #уведомление пользователя, создавшего тикет, об изменении статуса этого тикета


                if str(transition_value) == "done": #если тикет теперь закрыт
                    time_to_finish = my_jira.get_ticket_time(issue_key)
                    tickets_finished = 1
                    text = "Task " + issue_key + " was done." 
                    get_client().chat_postMessage(channel=f"@{reporter_id}", blocks=custom_messages.get_rating_blocks(text)) #отправка сообщения, в котором запрашивается оценка, пользователю, создавшему тикет


                if ticket_was_unread: #если тикет не был изменен до этого момента, происходит сбор статистики
                    time_to_start = my_jira.get_ticket_time(issue_key)
                    tickets_started = 1


                #обновление статистики в базе данных
                today = str(datetime.today().date())
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
                

                return "New status have been successfully applied"
            else:
                return "Status did not change"
    except:
        # print("User reacted to wrong message or some error occurred") 
        return "User reacted to wrong message or some error occurred" #пустые значения ключа тикета и создателя тикета вызвали ошибку


#ивент - открыта вкладка home
def app_home_opened(payload):
    user_id = payload["user"]
    update_blocks = []
    if my_functions.check_permission(user_id): #если пользователь обладает правами на изменения статуса тикета Jira
        import my_jira
        user_email = get_client().users_info(user=user_id)["user"]["profile"]["email"]
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


    return get_client().views_publish(user_id=user_id, view=custom_messages.get_app_home_view(update_blocks)) #вывод полученной информации на вкладке


#ивент - бот был удален пользователем
def app_uninstalled(payload):
    #удаление данных из базы для этого рабочего пространства
    team_id = get_client().api_call("auth.test")["team_id"]
    db.get_cluster().drop_database(team_id)
    # cluster["access_tokens"].drop_collection(TEAM_ID)