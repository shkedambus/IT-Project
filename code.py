@app.event("message")
def message(payload):
    if "subtype" not in payload.keys() and jira_connected():
        import my_jira
        channel_id = payload["channel"]
        is_im = client.conversations_info(channel=channel_id)["channel"]["is_im"]
        user_id = payload["user"]
        text = payload["text"]
        ts = payload["ts"]


        if user_id != BOT_ID and user_id != None and user_id != JIRA_ID and user_id != "USLACKBOT" and not is_im:
            issue_summary = cut_to_summary(text)
            user_name = client.users_info(user=user_id)["user"]["name"]
            description = user_name + ": " + text 
            my_jira.create_ticket(summary=issue_summary, description=description)


            issue_key = str(my_jira.search_ticket(summary=issue_summary))
            assignee = my_jira.get_ticket_assignee(issue_key)
            if assignee == "None":
                assignee = "Unassigned"
            current_status = str(my_jira.get_ticket_status(key=issue_key, field="name"))


            return client.chat_postMessage(channel=channel_id, thread_ts=ts,
                                        blocks=custom_messages.get_created_ticket_blocks(issue_key=issue_key, issue_summary=issue_summary, reporter_id=user_id, reporter_name=user_name, assignee=assignee, current_status=current_status))