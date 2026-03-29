import urllib.request

req = urllib.request.Request('http://13.51.107.61:8000/api/login', data=b'username=some@guy.com&password=password')
req.add_header('Content-Type', 'application/x-www-form-urlencoded')
try:
    resp = urllib.request.urlopen(req)
    print("Success:", resp.read())
except Exception as e:
    print(e)
    try:
        print(e.read().decode())
    except:
        pass
