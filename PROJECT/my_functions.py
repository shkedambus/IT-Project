import custom_messages
import my_db
from datetime import datetime
import time
import requests
from slack_client import get_client


#проверить домена и api токен Jira
def check_connection(domain, api_token, user_email):
    try:
        from my_jira import get_all_projects
        projects = get_all_projects(domain=domain, api_token=api_token, user_email=user_email)
        return projects
    except:
        return []


#проверить, подключена ли Jira
def jira_connected():
    return "jira" in my_db.db.get_db().list_collection_names() #возвращает True, если Jira подключена, иначе - False


#добавление стандартных реакций при подключении Jira к боту
def configure_reactions():
    import my_jira
    statuses = my_jira.miha_test_issue()
    emoji_dict = {"1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine"}
    data = [{"emoji": "exclamation", "transition_id": statuses[0]["transition_id"], "transition_name": statuses[0]["transition_name"], "transition_value": statuses[0]["transition_value"]}]
    for i in range(1, len(statuses) - 1):
        data.append({"emoji": emoji_dict[str(i)], "transition_id": statuses[i]["transition_id"], "transition_name": statuses[i]["transition_name"], "transition_value": statuses[i]["transition_value"]})
    data.append({"emoji": "white_check_mark", "transition_id": statuses[-1]["transition_id"], "transition_name": statuses[-1]["transition_name"], "transition_value": statuses[-1]["transition_value"]})
    status_data = {
        "value": 1,
        "status": statuses
    }
    my_db.update_db("reactions", data, True) #создаем коллекцию reactions (эмодзи - статус)
    my_db.update_db("statuses", status_data, False) #создаем коллекцию statuses (id статуса, название статуса, значение статуса)


#проверить пользователя на право изменения тикета Jira
def check_permission(user_id):
    return my_db.db.get_db()["users"].find_one({"user": user_id})["has_permission"] #возвращает True, если пользователь обладает правом на изменение тикета Jira, иначе - False


#найти id пользователя по его имени
def find_user_by_name(user_name):
    users = get_client().users_list()
    for user in users["members"]:
        if user["name"] == user_name:
            return user["id"] #возвращает id пользователя


#достать канал, в котором есть бот
def get_channel():
    channel_id = None
    for result in get_client().conversations_list():
        if channel_id is not None:
            break
        for channel in result["channels"]:
            if channel["is_member"]:
                channel_id = channel["id"]
                break
    return channel_id #возвращает id канала


#удалить приветствие из сообщения
def cut_hellos(words):
    hellos_list = ["привет", "здравствуй", "здравствуйте", "hi", "hello"] #список приветствий
    first_word = words[0]
    if "," in first_word or "." in first_word or "!" in first_word:
        first_word = first_word[:len(first_word) - 1]
    if first_word.lower() in hellos_list:
        return words[1:]
    return words


#обрезать сообщение пользователя для названия тикета в Jira
def cut_to_summary(text):
    text = str(text)
    text_list = text.split()
    text_list_without_hellos = cut_hellos(text_list)
    how_many_words = 6
    summary = " ".join(text_list_without_hellos[:how_many_words])
    return summary #возвращает summary тикета Jira (название тикета)


#отправить статистику за день каждый день в 20:00
def send_daily_stats():
    send_time = datetime.strptime("20:00:00", "%H:%M:%S")
    while True:
        current_time = datetime.strptime(datetime.today().strftime("%H:%M:%S"), "%H:%M:%S")
        if current_time == send_time:
            channel_id = get_channel()
            import my_jira
            result = my_jira.get_daily_stats_tickets()
            time_to_start = my_db.get_time_to_start()
            time_to_finish = my_db.get_time_to_finish()
            rating = my_db.get_rating()
            get_client().chat_postMessage(channel=channel_id,
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



#расписать пользователю про реакции и соответствующии им статусы Jira
def user_reactions(user_id, select_emoji=False):
    blocks = custom_messages.emoji_and_their_statuses(select_emoji)
    get_client().chat_postMessage(channel=f"@{user_id}", blocks=blocks) #вывод сообщения (эмодзи - статус)


#уведомить пользователя об изменении статуса тикета Jira
def notify_reporter(reporter_id, assignee_id, issue_key, old_status, new_status):
    import my_jira
    issue_summary = my_jira.get_ticket_summary(issue_key)


    assignee_name = get_client().users_info(user=assignee_id)["user"]["name"]
    
    if assignee_id != reporter_id:
        return get_client().chat_postMessage(channel=f"@{reporter_id}", 
                                    blocks=custom_messages.get_notification_blocks(issue_key=issue_key, issue_summary=issue_summary, old_status=old_status, new_status=new_status, user_id=assignee_id, user_name=assignee_name))
    #отправляем пользователю, создавшему тикет Jira, уведомление об изменении его статуса (тикет [тикет] был изменен [пользователь], старый статус: [старый статус], новый статус: [новый статус])


#получение списка всех эмодзи Slack
def slack_emojis():
    emojis_list = []
    response = requests.get(url="https://raw.githubusercontent.com/iamcal/emoji-data/master/emoji.json")
    emojis = response.json()
    for emoji in emojis:
        emojis_list.append(emoji["short_name"])
    return emojis_list