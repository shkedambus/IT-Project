from main import client, db
import custom_messages
import my_functions
import my_db


def info(ack, command):
    ack()
    user_id = command["user_id"]
    if my_functions.jira_connected(): #если Jira подключена
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
def commands(ack, command):
    ack()
    user_id = command["user_id"]
    return client.chat_postMessage(channel=f"@{user_id}", blocks=custom_messages.commands_blocks)


#комманда /unread-issues для получения непрочитанных тикетов
def unread_issues(ack, command):
    ack()
    user_id = command["user_id"]
    if my_functions.jira_connected(): #если Jira подключена
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
def update_issues(ack, command):
    ack()
    user_id = command["user_id"]
    if my_functions.jira_connected(): #если Jira подключена
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
def daily_stats(ack, command):
    ack()
    user_id = command["user_id"]
    if my_functions.jira_connected(): #если Jira подключена
        import my_jira
        #получение статистики
        result = my_jira.get_daily_stats_tickets()
        time_to_start = my_db.get_time_to_start()
        time_to_finish = my_db.get_time_to_finish()
        rating = my_db.get_rating()
        #вывод статистики
        return client.chat_postMessage(channel=f"@{user_id}", blocks=custom_messages.get_stats_blocks(created=str(result[0]), in_progress=str(result[1]), done=str(result[2]), unread=str(result[3]), avg_to_start=str(time_to_start // 60), avg_to_finish=str(time_to_finish // 60), rating=str(rating)))
    else:
        return client.chat_postMessage(channel=f"@{user_id}", blocks=custom_messages.jira_not_connected) #Jira не подключена


#комманда /select-time для выбора промежутка времени, после которого тикеты будут требовать обновления
def select_time_command(ack, command):
    ack()
    trigger_id = command["trigger_id"]
    return client.views_open(trigger_id=trigger_id, view=custom_messages.select_time_view) #запускается view для выбора промежутка времени