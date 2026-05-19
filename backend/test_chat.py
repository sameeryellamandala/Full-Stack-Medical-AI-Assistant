import requests
r = requests.post('http://127.0.0.1:8001/chat', data={'user_id': 'test', 'thread_id': 'thread_test', 'message': 'hello'})
print('STATUS:', r.status_code)
print('BODY:', r.text)
