#файл для получения списка всех эмодзи Slack


import requests


def get_emoji():
    emojis_list = []
    response = requests.get(url="https://raw.githubusercontent.com/iamcal/emoji-data/master/emoji.json")
    emojis = response.json()
    for emoji in emojis:
        emojis_list.append(emoji["short_name"])
    return emojis_list


# import json
# print(json.dumps(response.json(), indent=2))
# print(emojis_list)