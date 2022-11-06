#файл для формирования сообщений бота
from my_db import db
from slack_client import get_client


#onboarding message
onboarding_blocks = [
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "Hey there :wave: I'm Miha. I'm here to help you create and manage Jira issues in Slack."
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "*:one: Use the `Connect Jira` shortcut to connect Miha to your Jira project.*"
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "*:two: Use the `Select users` shortcut to give a user the permission to manage Jira issues (for administrators only).*"
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "*:three: Use the `Select emojis` shortcut to to select your own emojis for specific Jira statuses.*"
			}
		},
		{
			"type": "divider"
		},
		{
			"type": "context",
			"elements": [
				{
					"type": "mrkdwn",
					"text": ":eyes: View all the current Miha's settings with `/info`\n❓Get get all Miha's available commands with `/commands`"
				}
			]
		}
	]


connect_jira_shortcut_1 = {
	"type": "modal",
	"callback_id": "jira_1",
	"title": {
		"type": "plain_text",
		"text": "Miha & Jira"
	},
	"submit": {
		"type": "plain_text",
		"text": "Next"
	},
	"blocks": [
		{
			"type": "divider"
		},
		{
			"type": "input",
			"element": {
				"type": "plain_text_input",
				"action_id": "domain"
			},
			"label": {
				"type": "plain_text",
				"text": "Jira domain name"
			},
			"block_id": "domain"
		},
		{
			"type": "divider"
		},
		{
			"type": "input",
			"element": {
				"type": "plain_text_input",
				"action_id": "api"
			},
			"label": {
				"type": "plain_text",
				"text": "Jira API token"
			},
			"block_id": "api"
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "Create an API token from your Atlassian account:\n \t1. Log in to <https://id.atlassian.com/manage-profile/security/api-tokens>\n \t2. Click *Create API token*\n \t3. From the dialog that appears, enter a memorable and concise *Label* for your token and click *Create*\n \t4. Click *Copy to clipboard*, then paste the token to your script, or elsewhere to save:"
			}
		},
		{
			"type": "image",
			"title": {
				"type": "plain_text",
				"text": "Note: for security reasons it isn't possible to view the token after closing the creation dialog; if necessary, create a new token."
			},
			"image_url": "https://images.ctfassets.net/zsv3d0ugroxu/1RYvh9lqgeZjjNe5S3Hbfb/155e846a1cb38f30bf17512b6dfd2229/screenshot_NewAPIToken",
			"alt_text": "jira_api_token"
		}
	]
}


def connect_jira_shortcut_2(projects):
    options = []
    for project in projects:
        option = {
                    "text": {
                        "type": "plain_text",
                        "text": str(project),
                        "emoji": True
                    },
                    "value": str(project)
                }
        options.append(option)


    view = {
            "type": "modal",
            "callback_id": "jira_2",
            "title": {
                "type": "plain_text",
                "text": "Miha & Jira"
            },
            "submit": {
                "type": "plain_text",
                "text": "Submit"
            },
            "blocks": [
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "block_id": "static-select-action",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Connect your Jira project:"
                    },
                    "accessory": {
                        "type": "static_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Jira project",
                            "emoji": True
                        },
                        "options": options,
                        "action_id": "static_select-action"
                    }
                },
                {
                    "type": "section",
                    "block_id": "multi_conversations_select-action",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Select channel(s) for reporting and managing Jira issues:"
                    },
                    "accessory": {
                        "type": "multi_conversations_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select conversations"
                        },
                        "action_id": "multi_conversations_select-action"
                    }
                }
            ]
        }
    return view


connect_jira_shortcut_3 = {
	"type": "modal",
	"callback_id": "jira_3",
	"title": {
		"type": "plain_text",
		"text": "Miha & Jira"
	},
	"submit": {
		"type": "plain_text",
		"text": "Submit"
	},
	"blocks": [
		{
			"type": "divider"
		},
		{
			"type": "section",
			"block_id": "multi_users_select-action",
			"text": {
				"type": "mrkdwn",
				"text": "Select user(s) that will have the permission to manage Jira issues:"
			},
			"accessory": {
				"type": "multi_users_select",
				"action_id": "multi_users_select-action",
				"placeholder": {
					"type": "plain_text",
					"text": "Select users"
				}
			}
		}
	]
}


def show_result(text):
    result = {
        "type": "modal",
        "callback_id": "result",
        "title": {
            "type": "plain_text",
            "text": "Miha & Jira"
        },
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": text
                }
            }
        ]
    }
    return result


def emoji_and_their_statuses(select_emoji=False):
    if select_emoji:
        text = "Emojis for Jira statuses have been changed:"
    else:
        text = "*You were granted a permission to manage Jira issues by using Slack reactions.*"
    emoji_blocks = [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": text
                        }
                    },
                    {
                        "type": "divider"
		        }]


    collection_reactions = db.get_db()["reactions"]
    data = collection_reactions.find()
    for transition_dict in data:
        key = transition_dict["emoji"]
        value = collection_reactions.find({"emoji": key}).distinct("transition_name")[0]
        text = str(value) + " - " + ":" + str(key) + ":"
        block = {
			"type": "section",
			"text": {
				"type": "plain_text",
				"text": text,
				"emoji": True
			}
		}
        emoji_blocks.append(block)

    
    if not select_emoji:
        emoji_blocks.extend([{
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": '*You can select your own emojis for each Jira status by using `Select emojis` shortcut*'
                }
            }])
    return emoji_blocks


#относится к get_info_blocks (если Jira не подключена)
jira_not_connected = [
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "You have not connected Jira project yet."
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*You can do it by using 'Connect Jira' shortcut.*"
                    }
                }
            ]


def get_info_blocks(url, project, users, user_id, team_id):
    url_text = "Projects from site " + f"*<{url}|{url}>*"
    jira_connected = [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": ":electric_plug: Miha is connected to a Jira project:",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": url_text
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*" + project + "*"
                        }
                    },
                    {
                        "type": "divider"
                    }
                ]


    if users:
        jira_connected.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Following users can manage issue's status:*"
                        }
                    })
        fields = []
        for user in users:
            text_user = f"*<slack://user?team={team_id}&amp;id={user[0]}|@" + user[1] + ">*"
            fields.append({
					"type": "mrkdwn",
					"text": text_user
				})
        block = {
			"type": "section",
			"fields": fields
		}
        jira_connected.append(block)
        jira_connected.extend([{
                                    "type": "divider"
                                },
                                {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "*by using following Slack reactions:*"
                                }
                            }])

    else:
        jira_connected.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*You can give users permission to manage issues by using 'Select Users' shortcut.*"
                        }
                    })
        jira_connected.extend([{
                                    "type": "divider"
                                },
                                {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "*Selected users will be able to change Jira issues' statuses by using following Slack reactions:*"
                                }
                            }])


    blocks = emoji_and_their_statuses()
    emoji_blocks = blocks[2:-1]
    jira_connected.extend(emoji_blocks)


    hours = str(db.get_db()["users"].find_one({"user": user_id})["notification"])
    text_hours = "*Time period after which Jira issues should be updated - " + hours + " hours*"
    jira_connected.append({"type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": text_hours
                                }})


    return jira_connected


def get_rating_blocks(text):
    blocks = [
                {
                    "type": "section",
                    "block_id": "static_select-rating",
                    "text": {
                        "type": "plain_text",
                        "text": text
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "How much do you like the work done on the issue?"
                    },
                    "accessory": {
                        "type": "static_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select your rating"
                        },
                        "options": [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "1"
                                },
                                "value": "value-1"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "2"
                                },
                                "value": "value-2"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "3"
                                },
                                "value": "value-3"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "4"
                                },
                                "value": "value-4"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "5"
                                },
                                "value": "value-5"
                            }
                        ],
                        "action_id": "static_select-rating"
                    }
                }
	        ]
    return blocks


def get_notification_blocks(issue_key, issue_summary, old_status, new_status, user_id, user_name):
    team_id = get_client().api_call("auth.test")["team_id"]
    collection_jira = db.get_db()["jira"]
    domain = collection_jira.find_one()["domain"]


    text_issue_key = "*Issue:*\n" + f"*<https://{domain}.atlassian.net/browse/{issue_key}|{issue_key} {issue_summary}>*"
    text_old_status = "*Old status:*\n" + old_status
    text_new_status = "*New status:*\n" + new_status
    text_user = "*User:*\n" + f"*<slack://user?team={team_id}&amp;id={user_id}|@" + str(user_name) + ">*"
    blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Your issue was updated!"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": text_issue_key
                        },
                        {
                            "type": "mrkdwn",
                            "text": text_old_status
                        },
                        {
                            "type": "mrkdwn",
                            "text": text_user
                        },
                        {
                            "type": "mrkdwn",
                            "text": text_new_status
                        }
                    ]
                },
                {
                    "type": "divider"
                }
            ]
    return blocks


def get_created_ticket_blocks(issue_key, issue_summary, reporter_id, reporter_name, assignee, current_status):
    collection_jira = db.get_db()["jira"]
    domain = collection_jira.find_one()["domain"]

    team_id = get_client().api_call("auth.test")["team_id"]
    main_text = f"*<slack://user?team={team_id}&amp;id={reporter_id}|@" + reporter_name + ">*" + ' created a Task\n' + f"*<https://{domain}.atlassian.net/browse/{issue_key}|{issue_key} {issue_summary}>*"
    context_text = "Status: " + current_status + " | " + "Assignee: " + assignee + " | " + "Reporter: " + reporter_name
    blocks = [
                {
                    "type": "section",
                    "block_id": issue_key,
                    "text": {
                        "type": "mrkdwn",
                        "text": main_text
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "plain_text",
                            "text": context_text
                        }
                    ]
                }
	            ]
    return blocks


def get_unread_ticket_blocks(issue_key, issue_summary):
    collection_jira = db.get_db()["jira"]
    domain = collection_jira.find_one()["domain"]


    text = f"*<https://{domain}.atlassian.net/browse/{issue_key}|{issue_key} {issue_summary}>*"
    blocks = [
                {
                    "type": "section",
                    "block_id": issue_key,
                    "text": {
                        "type": "mrkdwn",
                        "text": text
                    }
                }
	        ]
    return blocks


def select_emoji_shortcut(statuses):
    blocks = [{
			"type": "section",
			"text": {
				"type": "plain_text",
				"text": "Enter emoji's shortname for each status. For example: white_check_mark :white_check_mark:",
				"emoji": True
			}
		},
		{
			"type": "divider"
		}]
    for status in statuses:
        block_id = str(status["transition_id"]) + "|" + str(status["transition_name"]) + "|" + str(status["transition_value"])
        block = {
                    "type": "input",
                    "block_id": block_id,
                    "element": {
                        "type": "plain_text_input",
                        "action_id": str(status["transition_id"])
                    },
                    "label": {
                        "type": "plain_text",
                        "text": str(status["transition_name"])
                    }
		        }
        blocks.append(block)
    view = {
                "type": "modal",
                "callback_id": "user_emoji",
                "title": {
                    "type": "plain_text",
                    "text": "Miha & Jira"
                },
                "submit": {
                    "type": "plain_text",
                    "text": "Submit"
                },
                "blocks": blocks
            }
    return view


select_time_view = {
                        "type": "modal",
                        "callback_id": "select-time",
                        "title": {
                            "type": "plain_text",
                            "text": "Miha & Jira"
                        },
                        "submit": {
                            "type": "plain_text",
                            "text": "Submit"
                        },
                        "blocks": [
                        {
                            "type": "input",
                            "block_id": "select-time",
                            "element": {
                                "type": "plain_text_input",
                                "action_id": "select-time"
                            },
                            "label": {
                                "type": "plain_text",
                                "text": "Enter time period after which issues should be updated (hours)"
                            }
                        }
                    ]
                }
                    

def get_stats_blocks(created, in_progress, done, unread, avg_to_start, avg_to_finish, rating):
    text = "• Created - " + created + " issues\n" + "• Done - " + done + " issues\n" + "• In progress - " + in_progress + " issues\n" + "• Unread - " + unread + " issues\n" + "\n" + "• Average assessment of the work performed - " + rating + "/5\n" + "• Average first response time - " + avg_to_start + " minutes\n" + "• Average resolution time - " + avg_to_finish + " minutes"
    blocks = [
                {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "The result of the work of the support team for today:"
                }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": text
                    }
                }
    ]
    return blocks


commands_blocks = [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Miha's available slash commands:"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*:one: Use the `/info` command to view all the current Miha's settings.*"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*:two: Use the `/unread-issues` command to get all unread Jira issues.*"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*:three: Use the `/update-issues` command to get Jira issues that need to be updated.*"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*:four: Use the `/daily-stats` command to get daily statistics of the work of the support team.*"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*:five: Use the `/select-time` command to select period of time after which Jira issues should be updated.*"
                        }
                    },
                    {
                        "type": "divider"
                    }
                ]


def get_app_home_view(update_blocks):
    blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ":wave: *Welcome to Miha*"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "Miha allows you to create Jira issues automatically and manage them via Slack reactions."
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": ":gear: Issues to update"
                            },
                            "value": "select-time",
                            "action_id": "select-time"
                        }
                    ]
                },
                {
                    "type": "divider"
                }
            ]
    blocks.extend(update_blocks)
    view = {
            "type": "home",
            "blocks": blocks
        }
    return view