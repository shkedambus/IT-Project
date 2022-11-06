import unittest
import my_functions


class TestMyFunctions(unittest.TestCase):

    def test_connect_jira_with_valid_credentials(self): 
        #подключение к Jira с действительными данными
        user_email = "donskoydmv@gmail.com"
        domain = "mmrfarm"
        api_token = "VNV84T2cHYKtyJS4xu6RC292"
        result = my_functions.check_connection(domain=domain, api_token=api_token, user_email=user_email)
        self.assertTrue(result)

    def test_connect_jira_with_invalid_api_token(self): 
        #подключение к Jira с недействительным API токеном
        user_email = "donskoydmv@gmail.com"
        domain = "mmrfarm"
        api_token = "1234567890"
        result = my_functions.check_connection(domain=domain, api_token=api_token, user_email=user_email)
        self.assertFalse(result)

    def test_connect_jira_with_invalid_domain(self): 
        #подключение к Jira с недействительным доменом
        user_email = "donskoydmv@gmail.com"
        domain = "1234567890"
        api_token = "VNV84T2cHYKtyJS4xu6RC292"
        result = my_functions.check_connection(domain=domain, api_token=api_token, user_email=user_email)
        self.assertFalse(result)

    def test_connect_jira_with_invalid_email(self): 
        #подключение к Jira с недействительной электронной почтой
        user_email = "1234567890"
        domain = "mmrfarm"
        api_token = "VNV84T2cHYKtyJS4xu6RC292"
        result = my_functions.check_connection(domain=domain, api_token=api_token, user_email=user_email)
        self.assertFalse(result)

    def test_cut_to_summary_with_long_text(self):
        text = "But I must explain to you how all this mistaken idea of denouncing pleasure and praising pain was born and I will give you a complete account of the system, and expound the actual teachings of the great explorer of the truth, the master-builder of human happiness. No one rejects, dislikes, or avoids pleasure itself, because it is pleasure, but because those who do not know how to pursue pleasure rationally encounter consequences that are extremely painful. Nor again is there anyone who loves or pursues or desires to obtain pain of itself, because it is pain, but because occasionally circumstances occur in which toil and pain can procure him some great pleasure. To take a trivial example, which of us ever undertakes laborious physical exercise, except to obtain some advantage from it? But who has any right to find fault with a man who chooses to enjoy a pleasure that has no annoying consequences, or one who avoids a pain that produces no resultant pleasure?"
        result = my_functions.cut_to_summary(text=text)
        self.assertEqual(result, "But I must explain to you")

    def test_cut_to_summary_with_short_enough_text(self):
        text = "On the other hand"
        result = my_functions.cut_to_summary(text=text)
        self.assertEqual(result, "On the other hand")

    def test_cut_to_summary_with_none_text(self):
        text = None
        self.assertRaises(Exception, my_functions.cut_to_summary, text)

    def test_cut_to_summary_with_empty_text(self):
        text = ""
        result = my_functions.cut_to_summary(text=text)
        self.assertEqual(result, "")

    def test_cut_to_summary_with_numbers(self):
        text = 1234567890
        result = my_functions.cut_to_summary(text=text)
        self.assertEqual(result, str(text))