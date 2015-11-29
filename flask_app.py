#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import json
import sys
import redis
reload(sys)
sys.setdefaultencoding('utf8')
from flask import Flask, url_for, session, request, redirect, Response, render_template
from flask_kvsession import KVSessionExtension
from simplekv.memory.redisstore import RedisStore
from nylas import APIClient

APP_ID = '86lwoxjfpc50e2m3aewqtd2qj'
APP_SECRET = 'i9lmxc0xhlvirot50rup6sgj'
redis_url = 'redis://rediscloud:u1ODHW41noA8sqMG@pub-redis-16921.us-east-1-4.6.ec2.redislabs.com:16921'
conn = redis.StrictRedis.from_url(redis_url)
store = RedisStore(conn)
app = Flask(__name__)
KVSessionExtension(store, app)
app.debug = True
app.secret_key = 'secret'

assert APP_ID != 'YOUR_APP_ID' or APP_SECRET != 'YOUR_APP_SECRET',\
    "You should change the value of APP_ID and APP_SECRET"

@app.route('/')
def index():
    if 'access_token' in session:
        return render_template('index.html')
    else:
    # We don't have an access token, so we're going to use OAuth to
        # authenticate the user

        # Ask flask to generate the url corresponding to the login_callback
        # route. This is similar to using reverse() in django.
        redirect_uri = url_for('.login_callback', _external=True)

        client = APIClient(APP_ID, APP_SECRET)
        return redirect(client.authentication_url(redirect_uri))

@app.route('/threads/contact/<email>/<int:offset>')
def threads_contact(email, offset):
    threads_contact = []
    client = APIClient(APP_ID, APP_SECRET, session['access_token'])
    while (len(threads_contact) + 1 <= (offset + 1) * 10):
        for thread in client.threads.where(in_='inbox', limit=20, any_email=email, view='expanded'):
            threadcounter = 0
            if len(thread.participants) <= 2:
                print thread.messages
                for message in thread.messages:
                    contact_message = {
                                'id': message['id'],
                                'date': message['date'],
                                'subject': message['subject'],
                                'name': message['from'][0]['name'], #thread.participants[0]['name'],
                                'email': message['from'][0]['email'], #thread.participants[0]['email'],
                                'snippet': message['snippet'],
                                'unread': message['unread'],
                                }
        #print thread.messages[0]
                    threads_contact.append(contact_message)
        threadcounter = threadcounter + 1
        if threadcounter < 20:
            last_thread = True
            break
    if offset == 0:
            start = 0
            end = 10
    else:
        start = offset * 10
        end = (offset + 1) * 10

    response = {'threads': threads_contact[start:end], 'lastThread': last_thread}
    js = json.dumps(response)
    resp = Response(js, status=200, mimetype='application/json')
    return resp



@app.route('/threads/contacts/<int:offset>')
def threads_contacts(offset):
    # If we have an access_token, we may interact with the Nylas Server
    #session['access_token'] = 'aC8stzQsDBR0ywlOmhCuyIBdu5uJYc'
    if 'access_token' in session:
        client = APIClient(APP_ID, APP_SECRET, session['access_token'])
        print session['access_token']
        if 'threads_contacts' not in session:
            session['threads_contacts'] = []
        if 'threads_contacts_addresses' not in session:
            session['threads_contacts_addresses'] = []
        if 'threads_contacts_offset' not in session:
            session['threads_contacts_offset'] = 0
        if 'threads_contacts_ids' not in session:
            session['threads_contacts_ids'] = []
        last_thread = False
        #session['threads_contacts'] = []
        #session['threads_contacts_addresses'] = []
        #session['threads_contacts_offset'] = 0
        #session['threads_contacts_ids'] = []
        while (len(session['threads_contacts']) + 1 < (offset + 1) * 10):
            threadcounter = 0

            for thread in client.threads.where(offset=session['threads_contacts_offset'], limit=99, in_='inbox'): #**{'in':'all', 'limit':40, 'offset':2}:
                threadcounter = threadcounter + 1
                if len(thread.participants) <= 2:
                    if len(thread.participants) == 1:
                        name = thread.participants[0]['name']
                        email = thread.participants[0]['email']
                    if len(thread.participants) == 2:
                        for participant in thread.participants:
                            if participant['email'] != 'andersdm@gmail.com':
                                name = participant['name']
                                email = participant['email']

                    if email not in session['threads_contacts_addresses'] and thread['id'] not in session['threads_contacts_ids']:
                                contact_thread = {
                                'id': thread['id'],
                                'date': thread['last_message_timestamp'],
                                'name': name, #thread.participants[0]['name'],
                                'email': email, #thread.participants[0]['email'],
                                'snippet': thread['snippet'],
                                'unread': thread['unread'],
                                'type': 'email'
                                }
                                session['threads_contacts'].append(contact_thread)
                                session['threads_contacts_addresses'].append(email)
                                session['threads_contacts_ids'].append(thread['id'])

                if (len(thread.participants) > 2) and (thread['id'] not in session['threads_contacts_ids']):
                    name = ''
                    emails = ''
                    for participant in thread.participants:
                        if participant['name']:
                            name += participant['name'] + ', '
                            emails += participant['email'] + ', '
                        else:
                            name += participant['email'] + ', '
                            emails += participant['email'] + ', '

                    contact_thread = {
                                'id': thread['id'],
                                'date': thread['last_message_timestamp'],
                                'name': name,
                                'email': emails,
                                'snippet': thread['snippet'],
                                'unread': thread['unread'],
                                'type': 'thread'
                                }
                    session['threads_contacts'].append(contact_thread)
                    session['threads_contacts_ids'].append(thread['id'])


            session['threads_contacts_offset'] = session['threads_contacts_offset'] + 1
            if threadcounter < 99:
                last_thread = True
                break

            # Return result to the client
        if offset == 0:
            start = 0
            end = 10
        else:
            start = offset * 10
            end = (offset + 1) * 10
        response = {'contacts': session['threads_contacts'][start:end], 'lastThread': last_thread}
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
    return redirect(url_for('threads_contacts', offset=0))

#if __name__ == '__main__':
#    app.run(host='0.0.0.0', port=8888)
