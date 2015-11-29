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
        threads = None
        while not threads:
            try:
                # Get the latest message from namespace zero.
                threads = client.threads.where(**{'in': 'all', 'limit': 20, 'offset':0, 'view':'expanded' })
                if not threads:  # A new account takes a little time to sync
                    print "No messages yet. Checking again in 2 seconds."
                    time.sleep(2)
            except Exception as e:
                print(e.message)
                return Response("<html>An error occurred.</html>")
        # Format the output
        text = 'mit navn det står med prikker'
        for thread in threads:
                    text += thread.snippet
        #text = "<html><h1>Here's a message from your inbox:</h1><b>From:</b> "
        #for sender in message["from"]:
        #    text += "{} &lt;{}&gt;".format(sender['name'], sender['email'])
        #text += "<br /><b>Subject:</b> " + message.subject
        #text += "<br /><b>Body:</b> " + message.body
        #text += "</html>"

        # Return result to the client
        return Response(text)
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
