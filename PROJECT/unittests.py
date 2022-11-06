import main
import my_jira
import my_functions
import my_db
import time
import os
import unittest
# from pathlib import Path
# from dotenv import load_dotenv
# env_path = Path(".") / ".env"
# load_dotenv(dotenv_path=env_path)


class TestMyFunctions(unittest.TestCase):

    def test_1(self): #подключение к Jira с действительными данными
        user_email = "donskoydmv@gmail.com"
        domain = "mmrfarm"
        api_token = "VNV84T2cHYKtyJS4xu6RC292"
        result = my_functions.check_connection(domain=domain, api_token=api_token, user_email=user_email)
        self.assertTrue(result)

    def test_2(self): #подключение к Jira с недействительным API токеном
        user_email = "donskoydmv@gmail.com"
        domain = "mmrfarm"
        api_token = "1234567890"
        result = my_functions.check_connection(domain=domain, api_token=api_token, user_email=user_email)
        self.assertFalse(result)

    def test_3(self): #подключение к Jira с недействительным доменом
        user_email = "donskoydmv@gmail.com"
        domain = "1234567890"
        api_token = "VNV84T2cHYKtyJS4xu6RC292"
        result = my_functions.check_connection(domain=domain, api_token=api_token, user_email=user_email)
        self.assertFalse(result)

    def test_4(self): #подключение к Jira с недействительной электронной почтой
        user_email = "1234567890"
        domain = "mmrfarm"
        api_token = "VNV84T2cHYKtyJS4xu6RC292"
        result = my_functions.check_connection(domain=domain, api_token=api_token, user_email=user_email)
        self.assertFalse(result)

    def test_5(self): #автоматическое создание тикета Jira в Slack на сообщение пользователя в канале для обработки обращений
        jira_issues_count_old = len(my_jira.get_all_tickets())
        message_payload = {'client_msg_id': 'cfc96bf5-1356-4738-be4c-9edd858897f9', 'type': 'message', 'text': 'TEST 5', 'user': 'U037RGRNS4D', 'ts': '1667662461.607839', 
                            'blocks': [{'type': 'rich_text', 'block_id': 'J1/S', 'elements': [{'type': 'rich_text_section', 'elements': [{'type': 'text', 'text': 'THIS IS MY MESSAGE FOR JIRA ISSUE'}]}]}], 
                            'team': 'T037UDKF6NN', 'channel': 'C049Q822LRJ', 'event_ts': '1667662461.607839', 'channel_type': 'channel'}
        main.message(message_payload)
        time.sleep(5)
        jira_issues_count_new = len(my_jira.get_all_tickets())
        result = jira_issues_count_new - jira_issues_count_old == 1
        self.assertTrue(result)

    def test_6(self): #автоматическое создание тикета Jira в Slack на сообщение пользователя в канале личных сообщений (ошибка)
        jira_issues_count_old = len(my_jira.get_all_tickets())
        message_payload = {'client_msg_id': 'cfc96bf5-1356-4738-be4c-9edd858897f9', 'type': 'message', 'text': 'TEST 6', 'user': 'U037RGRNS4D', 'ts': '1667662461.607839', 
                            'blocks': [{'type': 'rich_text', 'block_id': 'J1/S', 'elements': [{'type': 'rich_text_section', 'elements': [{'type': 'text', 'text': 'THIS IS MY MESSAGE FOR JIRA ISSUE'}]}]}], 
                            'team': 'T037UDKF6NN', 'channel': 'D037WPKD2CC', 'event_ts': '1667662461.607839', 'channel_type': 'channel'}
        try:
            main.message(message_payload)
            time.sleep(5)
            jira_issues_count_new = len(my_jira.get_all_tickets())
            result = jira_issues_count_new - jira_issues_count_old == 1
            self.assertFalse(result)
        except:
            self.assertFalse(False)
            
    def test_7(self): #уведомление об изменении тикета Jira в Slack пользователя, создавшего тикет (reporter_id == assignee_id - нет уведомления)
        reporter_id = "U037RGRNS4D"
        assignee_id = "U037RGRNS4D"
        issue_key = "IVR-265"
        old_status = "TO DO"
        new_status = "IN PROGRESS"
        result = my_functions.notify_reporter(reporter_id=reporter_id, 
                                              assignee_id=assignee_id, 
                                              issue_key=issue_key, 
                                              old_status=old_status, 
                                              new_status=new_status)
        self.assertIsNone(result)

    def test_8(self): #уведомление об изменении тикета Jira в Slack пользователя, создавшего тикет (reporter_id != assignee_id - уведомление)
        reporter_id = "U037RGRNS4D"
        assignee_id = "U03R0U1V1GT"
        issue_key = "IVR-265"
        old_status = "TO DO"
        new_status = "IN PROGRESS"
        result = my_functions.notify_reporter(reporter_id=reporter_id, 
                                              assignee_id=assignee_id, 
                                              issue_key=issue_key, 
                                              old_status=old_status, 
                                              new_status=new_status)
        self.assertIsNotNone(result)

    def test_9(self): #изменение статуса тикета Jira с помощью реакции на сообщение в Slack (сообщение пользователя, создавшего тикет, в канале для обработки обращений)
        reaction_payload = {'type': 'reaction_added', 'user': 'U037RGRNS4D', 'reaction': 'three', 
                            'item': {'type': 'message', 'channel': 'C049Q822LRJ', 'ts': '1667681517.797329'}, 
                            'item_user': 'U037RGRNS4D', 'event_ts': '1667681542.003100'}
        result = main.reaction_added(reaction_payload) == "New status have been successfully applied" or main.reaction_added(reaction_payload) == "Status did not change"
        self.assertTrue(result)

    def test_10(self): #изменение статуса тикета Jira с помощью реакции на сообщение в Slack (сообщение бота или сообщение в личном канале - вызов ошибки)
        reaction_payload = {'type': 'reaction_added', 'user': 'U037RGRNS4D', 'reaction': 'three', 
                            'item': {'type': 'message', 'channel': 'C049Q822LRJ', 'ts': '1667681528.464159'}, 
                            'item_user': 'U037UDE9ASX', 'event_ts': '1667681610.003200'}
        result = main.reaction_added(reaction_payload) == "User reacted to wrong message or some error occurred"
        self.assertTrue(result)

    def test_11(self): #получение рейтинга из базы данных
        result = my_db.get_rating()
        self.assertIsNotNone(result)

    def test_12(self): #получение среднего времени до взятия тикета в работу из базы данных
        result = my_db.get_time_to_start()
        self.assertIsNotNone(result)

    def test_13(self): #получение среднего времени до закрытия тикета из базы данных
        result = my_db.get_time_to_finish()
        self.assertIsNotNone(result)

    def test_14(self): #получение id пользователя из его имени (существующий пользователь)
        user_name = "donskoydmv"
        result = my_functions.find_user_by_name(user_name=user_name)
        self.assertIsNotNone(result)

    def test_15(self): #получение id пользователя из его имени (несуществущий пользователь)
        user_name = "unknown user"
        result = my_functions.find_user_by_name(user_name=user_name)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()