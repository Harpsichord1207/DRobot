import config
import requests
import time

from utils import get_user_id


class ToDoManager:
    token = None

    @classmethod
    def _post(cls, url, payload, _token=None, retry_times=5):
        while retry_times:
            try:
                token = _token or cls.token or cls.get_token()
                url += '?access_token={}'.format(token)
                resp = requests.post(url, json=payload).json()
                assert resp.get('sub_msg') != '不合法的access_token'
                return resp
            except AssertionError:
                cls.get_token()
                retry_times -= 1

    @classmethod
    def get_token(cls):
        url = 'https://oapi.dingtalk.com/gettoken'
        resp = requests.get(url, params=dict(appkey=config.DING_APP_KEY, appsecret=config.DING_APP_SECRET)).json()
        cls.token = resp.get('access_token')
        return cls.token

    @classmethod
    def get_todo(cls, user_id, _token=None):
        payload = {
            'userid': user_id,
            'offset': 0,
            'limit': 50,
            'status': 0
        }
        url = 'https://oapi.dingtalk.com/topapi/workrecord/getbyuserid'
        return cls._post(url, payload, _token)

    @classmethod
    def delete_todo(cls, user_id, record_id, _token=None):
        payload = {
            'record_id': record_id,
            'userid': user_id
        }
        url = 'https://oapi.dingtalk.com/topapi/workrecord/update'
        return cls._post(url, payload, _token)

    @classmethod
    def add_todo(cls, params=None, _token=None):

        if params is None:
            return {}

        payload = {
            'userid': get_user_id(params['assignee']),
            'create_time': int(time.time() * 1000),
            'title': params['title'],
            'url': params['url'],
            'formItemList': {
                'title': params['title'],
                'content': params['content']
            },
            'originator_user_id': get_user_id(params['user'])
        }

        url = 'https://oapi.dingtalk.com/topapi/workrecord/add'
        return cls._post(url, payload, _token)

