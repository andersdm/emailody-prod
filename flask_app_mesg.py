import time
import json
from flask import Flask, url_for, session, request, redirect, Response

from nylas import APIClient

APP_ID = '86lwoxjfpc50e2m3aewqtd2qj'
APP_SECRET = 'i9lmxc0xhlvirot50rup6sgj'
app = Flask(__name__)
app.debug = True
app.secret_key = 'secret'

assert APP_ID != 'YOUR_APP_ID' or APP_SECRET != 'YOUR_APP_SECRET',\
    "You should change the value of APP_ID and APP_SECRET"


@app.route('/messages/<int:pagenr>')
def index(pagenr):
    session['contact_mails'] = []
    session['contact_addresses'] = []
    offset = pagenr
    # If we have an access_token, we may interact with the Nylas Server
    if 'access_token' in session:
        client = APIClient(APP_ID, APP_SECRET, session['access_token'])
        message = None
        while len(session['contact_addresses']) + 1 < pagenr * 10:
            try:
                # Get the latest message from namespace zero.
                messages = client.messages.where(**{'in': 'all', 'limit': 20, 'offset':offset})
                for message in messages:
                    #print message['from'][0]['email']
                    if message['from'][0]['email'] not in session['contact_addresses']:
                        contact_mail = {
                        'id': len(session['contact_addresses']),
                        'date': message['date'],
                        'name': message['from'][0]['name'],
                        'email': message['from'][0]['email'],
                        'snippet': message['snippet'],
                        'unread': message['unread']
                        }
                        session['contact_mails'].append(contact_mail)
                        session['contact_addresses'].append(message['from'][0]['email'])
                #if messages.sender[0]['email'] not in session['emails']:
                if not messages:  # A new account takes a little time to sync
                    print "No messages yet. Checking again in 2 seconds."
                    time.sleep(2)
            except Exception as e:
                print(e.message)
                return Response("<html>An error occurred.</html>")
            offset += 1
        if pagenr - 1 == 0:
            start = 0
            end = 10
        else:
            start = (pagenr - 1) * 10
            end = pagenr * 10


        response = {'contacts': session['contact_mails'][start:end]}
        js = json.dumps(response)
        resp = Response(js, status=200, mimetype='application/json')
        return resp

    else:
        # We don't have an access token, so we're going to use OAuth to
        # authenticate the user

        # Ask flask to generate the url corresponding to the login_callback
        # route. This is similar to using reverse() in django.
        redirect_uri = url_for('.login_callback', _external=True)

        client = APIClient(APP_ID, APP_SECRET)
        return redirect(client.authentication_url(redirect_uri))
@app.route('/login_callback')
def login_callback():
    if 'error' in request.args:
        return "Login error: {0}".format(request.args['error'])

    # Exchange the authorization code for an access token
    client = APIClient(APP_ID, APP_SECRET)
    code = request.args.get('code')
    session['access_token'] = client.token_for_code(code)
    return index(1)

#if __name__ == '__main__':
#    app.run(host='0.0.0.0', port=8888)
