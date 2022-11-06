from slack_client import get_client
import custom_messages
import my_functions
from my_db import db, update_db


#view для первого этапа подключения Jira к боту (ввод доменного имя и api ключа Jira)
def jira_1(ack, body, view, logger):
    trigger_id = body["trigger_id"]
    user_id = body["user"]["id"]
    user_email = get_client().users_info(user=user_id)["user"]["profile"]["email"]
    domain = view["state"]["values"]["domain"]["domain"]["value"]
    api_token = view["state"]["values"]["api"]["api"]["value"]
    ack()
    if my_functions.check_connection(domain=domain, api_token=api_token, user_email=user_email):
        import my_jira
        projects = my_jira.get_all_projects(domain=domain, api_token=api_token, user_email=user_email)
        db["temp"].insert_one({"domain": domain, "api_key": api_token, "email": user_email})
        return get_client().views_open(trigger_id=trigger_id, view=custom_messages.connect_jira_shortcut_2(projects)) #запускает view для второго этапа подключения Jira к боту
    else:
        return get_client().views_open(trigger_id=trigger_id, view=custom_messages.show_result(text=":warning: Wrong Jira domain name or API token.")) #показывает ошибку, если доменное имя или api токен недействительны


#view для второго этапа подключения Jira к боту (выбор проекта Jira и канала для обработки обращений)
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


    get_client().chat_postMessage(channel=f"@{user_id}", text="Jira has been successfully connected!")
    get_client().views_open(trigger_id=trigger_id, view=custom_messages.connect_jira_shortcut_3)


    selected_channels = view["state"]["values"]["multi_conversations_select-action"]["multi_conversations_select-action"]["selected_conversations"]
    print(selected_channels)
    for selected_channel in selected_channels:
        try:
            is_im = get_client().conversations_info(channel=str(selected_channel))["channel"]["is_im"]
            if not is_im:
                get_client().conversations_join(channel=selected_channel) #бот заходит в выбранный пользователем канал для обработки сообщений
                get_client().chat_postMessage(channel=selected_channel, blocks=custom_messages.onboarding_blocks) #бот отправляет сообщение, что Jira была успешно подключена
        except:
            print("")


#view для третьего этапа подключения Jira к боту (выбор пользователей, которые могут изменять статус тикета Jira)
def jira_3(ack, body, view, logger):
    ack()


    my_functions.configure_reactions()
    selected_users = view["state"]["values"]["multi_users_select-action"]["multi_users_select-action"]["selected_users"] #список выбранных пользователей
    all_users = get_client().users_list()["members"] #список всех пользователей
    newvalues = []
    for object in all_users:
        user = object["id"]
        myquery = db["users"].find_one({"user": user})
        if user in selected_users:
            #выдача прав пользователям, которые были выбраны
            if not get_client().users_info(user=user)["user"]["is_bot"] and not user == "USLACKBOT":  #если пользователь не бот

                
                email = myquery["email"]
                notification = myquery["notification"]
                newvalues.append({"user": user, "email": email, "notification": notification, "has_permission": True})
                my_functions.user_reactions(user)
        else:
            #обнуление прав пользователям, которые не были выбраны
            if not get_client().users_info(user=user)["user"]["is_bot"] and not user == "USLACKBOT": #если пользователь не бот

                
                email = myquery["email"]
                notification = myquery["notification"]
                newvalues.append({"user": user, "email": email, "notification": notification, "has_permission": False})
    return update_db("users", newvalues, True) #обновление базы данных


#view для получения эмодзи пользователя
def user_emoji(ack, body, view, logger):
    ack()
    # user_id = body["user"]["id"]
    trigger_id = body["trigger_id"]
    slack_emojis = my_functions.slack_emojis() #берем список всех эмодзи Slack из файла my_functions.py
    custom_emojis = list(get_client().emoji_list()["emoji"].keys()) #берем список всех пользовательских эмодзи Slack
    all_emojis = slack_emojis
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
                return get_client().views_open(trigger_id=trigger_id, view=custom_messages.show_result(text=":warning: Invalid input\nTrying to apply identical emoji to different Jira statuses")) #вывод сообщения об ошибке (один и тот же эмодзи для нескольких статусов)
        else:
            return get_client().views_open(trigger_id=trigger_id, view=custom_messages.show_result(text=f':warning: Invalid input\nEmoji "{emoji}" does not exist')) #вывод сообщения об ошибке (недействительный эмодзи)
    update_db("reactions", data, True)
    get_client().views_open(trigger_id=trigger_id, view=custom_messages.show_result(text="All changes have been successfully applied!")) #вывод сообщения, что все изменения были успешно применены
    users = db["users"].find({"has_permission": True}).distinct("user")
    for user in users: #уведомление каждого пользователя, обладающего правами по изменению статуса тикета Jira, об изменении эмодзи для статусов тикетов Jira
        my_functions.user_reactions(user, True)


#view для выбора промежутка времени
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
        return get_client().views_open(trigger_id=trigger_id, view=custom_messages.show_result(text="All changes have been successfully applied!")) #все изменения были успешно применены
    except:
        return get_client().views_open(trigger_id=trigger_id, view=custom_messages.show_result(text=":warning: Invalid input.")) #пользователь ввел недействительные данные