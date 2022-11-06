from datetime import datetime, timedelta
from jira import JIRA
import pytz
from my_db import db


#часовой пояс для сравнения времени
utc = pytz.UTC 


#для Jira
jira_options = None
jira = None
jql = None


#проверить пользователя на право изменения тикета
def check_permission(user_email):
    return db.get_db()["users"].find_one({"email": user_email})["has_permission"]


#достать все проекты в Jira
def get_all_projects(domain, api_token, user_email):
    url = "https://" + domain + ".atlassian.net"
    jira_options = {"server": url}
    jira = JIRA(options=jira_options, basic_auth=(user_email, api_token))
    return jira.projects()


#подключить Jira
def initialize_jira():
    myquery = db.get_db()["jira"].find_one()
    domain = myquery["domain"]
    api_key = myquery["api_key"]
    email = myquery["email"]
    project = myquery["project"]
    url = "https://" + domain + ".atlassian.net"

    
    global jira_options, jira, jql
    jira_options = {"server": url}
    jira = JIRA(options=jira_options, basic_auth=(email, api_key))
    jql = "project = " + project
    

#создать тикет
def create_ticket(summary, description=""):
    initialize_jira()
    issue_dict = {
        'project': db.get_db()["jira"].find_one()["project"],
        'summary': summary,  
        'description': description,
        'issuetype': {'name': 'Task'}
    }
    return jira.create_issue(fields=issue_dict)


#удалить тикет
def delete_ticket(key):
    initialize_jira()
    return jira.issue(key).delete()


#достать все тикеты
def get_all_tickets():
    initialize_jira()
    return jira.search_issues(jql)


#найти определенный тикет
def search_ticket(summary):
    issues_list = get_all_tickets()
    for issue in issues_list:
        if summary == issue.raw["fields"]["summary"]:
            return issue


#достать все статусы
def get_all_statuses():
    initialize_jira()
    issue = jira.search_issues(jql)[0]
    transitions = jira.transitions(issue)
    statuses = []
    indeterminate_statuses = []
    # for transition in transitions:
    #     statuses.append({"transition_id": transition["id"], "transition_name": transition["name"], "transition_value": transition["to"]["statusCategory"]["key"]})
    for transition in transitions:
        if transition["to"]["statusCategory"]["key"] == "new":
            statuses.append({"transition_id": transition["id"], "transition_name": transition["name"], "transition_value": "new"})
    for transition in transitions:
        if transition["to"]["statusCategory"]["key"] == "indeterminate":
            indeterminate_statuses.append({"transition_id": transition["id"], "transition_name": transition["name"], "transition_value": "indeterminate"})
    indeterminate_statuses.reverse()
    statuses.extend(indeterminate_statuses)
    for transition in transitions:
        if transition["to"]["statusCategory"]["key"] == "done":
            statuses.append({"transition_id": transition["id"], "transition_name": transition["name"], "transition_value": "done"})
    return statuses


#достать все названия тикетов (для проверки на создание тикетов с одним и тем же названием)
def get_all_summaries():
    initialize_jira()
    summaries = []
    all_issues = get_all_tickets()
    for issue in all_issues:
        ticket = jira.issue(issue)
        summary = get_ticket_summary(ticket)
        summaries.append(summary)
    return summaries


#изменить статус тикета
def change_status(key, status, user):
    initialize_jira()
    issue = jira.issue(key)
    jira.assign_issue(issue, user)
    return jira.transition_issue(key, status)


def miha_test_issue():
    # initialize_jira()
    issues_list = get_all_tickets()
    if issues_list:
        statuses = get_all_statuses()
    else:
        issue = create_ticket(summary="Miha test issue")
        statuses = get_all_statuses()
        issue.delete()
    return statuses


#достать текущий статус тикета
def get_ticket_status(key, field="id"):
    initialize_jira()
    issue = jira.issue(key)
    transitions = jira.transitions(issue)
    status = issue.fields.status
    for transition in transitions:
        if str(transition["to"]["name"]) == str(status):
            return transition[field]


#достать пользователя, который создал тикет
def get_ticket_reporter(key):
    initialize_jira()
    issue = jira.issue(key)
    reporter = str(issue.fields.reporter)
    return reporter


#достать пользователя, на которого забиндили тикет
def get_ticket_assignee(key):
    initialize_jira()
    issue = jira.issue(key)
    assignee = str(issue.fields.assignee)
    return assignee
    # if assignee:
    #     return assignee
    # else:
    #     return "Unassigned"


#достать название тикета
def get_ticket_summary(key):
    initialize_jira()
    issue = jira.issue(key)
    summary = str(issue.fields.summary)
    return summary


#достать непрочитанные тикеты
def get_unread_tickets():
    initialize_jira()
    result = {}
    issues = get_all_tickets()
    for issue in issues:
        fields = issue.raw["fields"]
        if fields["resolution"]:
            continue
        updated = fields["updated"]
        created = fields["created"]
        if created == updated:
            result[str(issue)] = [fields["summary"], fields["description"]]
    return result


#достать тикеты, требующие обновления
def get_unupdated_tickets(user_id, user_email):
    initialize_jira()
    today = datetime.today()


    result = {}
    issues = get_all_tickets()
    for issue in issues:
        fields = issue.raw["fields"]


        if fields["resolution"]:
            continue
        updated = datetime.strptime(fields["updated"], '%Y-%m-%dT%H:%M:%S.%f%z')
        hours = db.get_db()["users"].find_one({"user": user_id})["notification"]
        if utc.localize(today - timedelta(hours=hours)) >= (updated).replace(tzinfo=utc):
            result[str(issue)] = [fields["summary"], fields["description"]]
    return result


# достать статистику по тикетам
def get_daily_stats_tickets():
    initialize_jira()
    today = datetime.today().date()
    all_created = 0
    in_progress = 0
    done = 0
    unread = 0


    issues = get_all_tickets()
    for issue in issues:
        fields = issue.raw["fields"]


        created = datetime.strptime(fields["created"], '%Y-%m-%dT%H:%M:%S.%f%z')
        if created.date() == today:
            all_created += 1


        if fields["resolution"]: #если тикет был закрыт
            resolution_date = datetime.strptime(fields["resolutiondate"], '%Y-%m-%dT%H:%M:%S.%f%z').date()
            if resolution_date == today:
                done += 1
                continue
        

        updated = datetime.strptime(fields["updated"], '%Y-%m-%dT%H:%M:%S.%f%z')
        if updated.date() == today:
            if updated != created:
                in_progress += 1
            else:
                unread += 1

    
    return [all_created, in_progress, done, unread]


#проверить тикет на первое обновление
def if_ticket_unread(ticket):
    initialize_jira()
    issue = jira.issue(ticket)
    fields = issue.raw["fields"]
    created = datetime.strptime(fields["created"], '%Y-%m-%dT%H:%M:%S.%f%z')
    updated = datetime.strptime(fields["updated"], '%Y-%m-%dT%H:%M:%S.%f%z')
    return created == updated


#достать время до взятия тикета в работу/время до закрытия тикета
def get_ticket_time(ticket):
    initialize_jira()
    issue = jira.issue(ticket)
    fields = issue.raw["fields"]
    created = datetime.strptime(fields["created"], '%Y-%m-%dT%H:%M:%S.%f%z')
    updated = datetime.strptime(fields["updated"], '%Y-%m-%dT%H:%M:%S.%f%z')
    return int((updated - created).total_seconds())