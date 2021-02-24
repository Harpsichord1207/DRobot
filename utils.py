import config
import requests


def ding_send(msg):
    url = 'https://oapi.dingtalk.com/robot/send?access_token={}'.format(config.DING_WEBHOOK_TOKEN)
    content = dict(content='{}'.format(msg))
    data = dict(msgtype='text', text=content)
    requests.post(url=url, json=data)


def get_user_id(gitlab_username):
    if gitlab_username not in config.GITLAB_DING_USER_MAPPING:
        raise ValueError('Invalid Username: {}'.format(gitlab_username))
    return config.GITLAB_DING_USER_MAPPING[gitlab_username]
