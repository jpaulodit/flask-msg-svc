import pprint
from collections import namedtuple
from flask import Flask, request, jsonify, current_app, make_response
from functools import update_wrapper
from datetime import timedelta

app = Flask(__name__)

msg_list = []
Msg = namedtuple('Msg', ['timestamp', 'user_id', 'lecture_id', 'message', 'author_type'])


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, str):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, str):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers
            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/save_msg', methods=['POST'])
@crossdomain(origin='*')
def save_msg():
    if request.is_json:
        data = request.get_json()

        timestamp = data.get('timestamp')
        user_id = data.get('user_id')
        lecture_id = data.get('lecture_id')
        message = data.get('message')
        author_type = data.get('type')

        # save the data to persistent storage
        msg_list.append(Msg(timestamp, user_id, lecture_id, message, author_type))
        pprint.pprint(msg_list)

    return ''


@app.route('/get_msg_list', methods=['GET'])
@crossdomain(origin='*')
def get_messages():
    lecture_id = int(request.args.get('lecture_id', 0))
    timestamp_start = int(request.args.get('ts_start', 0))
    timestamp_end = int(request.args.get('ts_end', -1))  # return all by default

    if not lecture_id:
        return 'missing lecture_id', 400

    if timestamp_end != -1 and timestamp_start >= timestamp_end:
        return 'invalid timestamp range', 400

    if timestamp_end == -1:
        filter_func = lambda x: x.lecture_id == lecture_id \
                                and x.timestamp >= timestamp_start
    else:
        filter_func = lambda x: x.lecture_id == lecture_id \
                                and timestamp_start <= x.timestamp <= timestamp_end

    result_list = list(filter(filter_func, msg_list))

    return jsonify([result._asdict() for result in result_list])

if __name__ == '__main__':
    msg_list.append(Msg(1, 'KittenLove84', 1000, 'OMG kittens!!!', 'student'))
    msg_list.append(Msg(3, 'SmittenKitten86', 1000, 'OMG more kittens!!!', 'student'))
    msg_list.append(Msg(5, 'PuppyFan85', 1000, 'Where\re the puppies???', 'student'))
    app.run(debug=True, host='0.0.0.0')
