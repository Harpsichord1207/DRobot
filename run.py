import pathlib
import subprocess
import waitress

from flask import Flask, jsonify, request, abort
from todo import ToDoManager
from utils import ding_send, get_user_id


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def root():
    if request.method == 'GET':
        abort(404)
    data = request.json
    print('---get command---')
    print(data)
    print('-----------------')
    content = data.get('text', {}).get('content')
    if str(content).strip() == '获取所有待办':
        todos = ToDoManager.get_todo(data.get('senderStaffId'))
        try:
            s = []
            for i, record in enumerate(todos['records']['list']):
                s.append('{}.{}'.format(i+1, record['title']))
            s = '\n'.join(s)
        except KeyError:
            s = '无待办'
    elif str(content).strip() == '删除所有待办':
        todos = ToDoManager.get_todo(data.get('senderStaffId'))
        try:
            for record in todos['records']['list']:
                ToDoManager.delete_todo(data.get('senderStaffId'), record['record_id'])
        except KeyError:
            pass
        s = 'OK'
    elif str(content).strip().startswith('imedia') or str(content).strip().startswith('jdy'):
        sh_file = pathlib.Path(__file__).parent.joinpath("shell").joinpath("run_command.sh")
        if not sh_file.exists():
            s = "未找到shell/run_command.sh"
        else:
            cmd = 'bash {} {}'.format(sh_file, str(content).strip())
            output = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            s = ''
            s += output.stdout.decode('utf-8')
            s += '\n{}'.format(output.stderr.decode('utf-8'))
    else:
        s = f"Hello [{data.get('senderNick')}], your command is [{content}]"

    message = {
        "msgtype": "text",
        "text": {
            "content": s.strip()
        }
    }

    return jsonify(message)


@app.route('/hooks', methods=['GET', 'POST'])
def hook():
    if request.method == 'GET':
        abort(404)
    data = request.json
    print('---get issue hook---')
    print(data)
    print('--------------------')
    if not isinstance(data, dict):
        abort(404)
    if data.get('object_kind') != 'issue' or data.get('event_type' != 'issue'):
        print('not issue event!')
        abort(404)
    if data.get('project', {}).get('name') != 'drobot':
        print('not drobot repo!')
        abort(404)

    action = data['object_attributes']['action']  # open or close
    user = data['user']['username']
    assignee = data['assignees'][0]['username']
    title = data['object_attributes']['title']
    url = data['object_attributes']['url']
    content = data['object_attributes']['description']

    resp = {}
    if action == 'open':
        resp = ToDoManager.add_todo(
            params=dict(assignee=assignee, user=user, title=title, url=url, content=content)
        )
        ding_send('Gitlab新增任务[{}/{}]，已同步到钉钉待办'.format(title, assignee))
    elif action == 'close':
        record_id = None
        user_id = get_user_id(assignee)
        all_todos = ToDoManager.get_todo(user_id)
        for record in all_todos.get('records', {}).get('list', []):
            if record.get('url') == url:
                record_id = record['record_id']
                break
        if record_id:
            resp = ToDoManager.delete_todo(user_id, record_id)
            ding_send('Gitlab删除任务[{}/{}]，已同步到钉钉待办'.format(title, assignee))

    print('---action response---')
    print(resp)
    print('---------------------')
    return jsonify(resp)


if __name__ == '__main__':
    import sys
    host = '0.0.0.0'
    port = 9099
    try:
        if sys.argv[1] == '--debug':
            app.run(host=host, port=port, debug=True)
    except IndexError:
        waitress.serve(app, host='0.0.0.0', port=9099, threads=2)
