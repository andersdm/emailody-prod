# -*- coding: utf-8 -*-
import os
import logging
import sys
import httplib2
import re
import json
import redis
import urllib
from flask import Flask, abort, redirect, url_for, Response, render_template, session, request
#from flask.ext.sqlalchemy import SQLAlchemy
#from sqlalchemy.dialects.postgresql import JSON
from rq import Queue
from rq.job import Job
from worker import conn
from googleapiclient import discovery
from googleapiclient.http import BatchHttpRequest
from oauth2client import client
from flask_kvsession import KVSessionExtension
from simplekv.memory.redisstore import RedisStore
store = RedisStore(redis.StrictRedis())
app = Flask(__name__)
KVSessionExtension(store, app)
#app.config['SESSION_TYPE'] = 'memcached'
from messages import get_messages
app.config['SECRET_KEY'] = 'super secret key'
app.debug = True
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)
#app.config.from_object(os.environ['APP_SETTINGS'])
#db = SQLAlchemy(app)

q = Queue(connection=conn)
#from contacts import get_messages

#from models import *



@app.route('/')
def index():
    if 'contactsNextPageToken' not in session:
        session['contactsNextPageToken'] = 0
    if 'contacts' not in session:
        session['contacts'] = []
    if 'seen' not in session:
        session['seen'] = []
    if 'mails' not in session:
        session['mails'] = []
    if 'credentials' not in session:
        return redirect(url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    if credentials.access_token_expired:
        return redirect(url_for('oauth2callback'))
    else:
        return render_template('index.html')



@app.route('/oauth2callback')
def oauth2callback():
    flow = client.flow_from_clientsecrets('client_secrets.json',
            scope='https://www.googleapis.com/auth/gmail.readonly',
redirect_uri=url_for('oauth2callback',_external=True))
    if 'code' not in request.args:
        auth_uri = flow.step1_get_authorize_url()
        return redirect(auth_uri)
    else:
        auth_code = request.args.get('code')
        credentials = flow.step2_exchange(auth_code)
        session['credentials'] = credentials.to_json()
        return redirect(url_for('index'))


@app.route('/v1/gmail/contacts/<int:pagenr>')
def contacts(pagenr):    
	# Authorize the httplib2.Http object with our credentials	
    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    
    http = credentials.authorize(httplib2.Http())

# Build the Gmail service from discovery

    gmail_service = discovery.build('gmail', 'v1', http=http)
    print session['seen']
    while (len(session['seen'])+1 < pagenr*10):
        print len(session['seen'])
        
# Retrieve a page of threads

        

# Print ID for each thread
# if threads['threads']:
#  for thread in threads['threads']:
#    print 'Thread ID: %s' % (thread['id'])

        def contactscallbackfunc(result, results, moreresults):
        
       # in old Python versions:
       # if seen.has_key(marker)
       # but in new ones:

            if 'UNREAD' in results['labelIds']:
                Unread = 'true'
            else:
                Unread = 'false'
            for header in results['payload']['headers']:
                if header['name'] == 'Date':
                    Date = header['value']
                if header['name'] == 'From':
                    From = header['value']
                    address = From.split()[-1]
                    address = re.sub(r'[<>]', '', address)
                    Address = address.strip()
                    Name = From.rsplit(' ', 1)[0]
                
                

            if From not in session['seen']:
                job = q.enqueue_call(func=get_messages, args=(0,From.replace('\"',''), session['credentials']), result_ttl=5000)
                Contact = {
                    'jobId': str(job.get_id()),
                    'messageId': results['id'],
                    'date': Date,
                    'name': Name,
                    'address': Address,
                    'snippet': results['snippet'],
                    'unread': Unread
                    }
                session['contacts'].append(Contact)
                session['seen'].append(From)
        
        message_ids = gmail_service.users().messages().list(userId='me', maxResults=20, labelIds='INBOX', pageToken=session['contactsNextPageToken']).execute()
        batchContacts = BatchHttpRequest(callback=contactscallbackfunc)
        #return message_ids['messages'][0]['id']
        session['contactsNextPageToken'] = message_ids['nextPageToken']
        for msg_id in message_ids['messages']:
            batchContacts.add(gmail_service.users().messages().get(userId='me', id=msg_id['id'], format='metadata', metadataHeaders=['from', 'date']))
        batchContacts.execute()
        
        

    #return "test"


    #def mailscallbackfunc(result, results, moreresults):
    #    if 'UNREAD' in results['labelIds']:
    #        Unread = 'true'
    #   else:
    #        Unread = 'false'
    #
    #batchMails = BatchHttpRequest(callback=mailscallbackfunc)
    #for contact in session['seen']:
	#	batchContacts.add(gmail_service.users().messages().get(userId='me',
    #              id=msg_id['id'], format='metadata',
    #              metadataHeaders=['from', 'date']))
    #batchMails.execute()
    if pagenr - 1 == 0:
        start = 0
        end = 9
    else:
        start = (pagenr - 1) * 10 -1 
        end = pagenr * 10 -1
    response = {'nextPageToken': session['contactsNextPageToken'], 'contacts': session['contacts'][start:end]} 
    js = json.dumps(response)
    resp = Response(js, status=200, mimetype='application/json')
    print len(session['seen'])
    return resp
	
@app.route('/v1/gmail/message/<msg_id>')
def message(msg_id):
    if 'credentials' not in session:
        return redirect(url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    if credentials.access_token_expired:
        return redirect(url_for('oauth2callback'))
    # Authorize the httplib2.Http object with our credentials

    http = credentials.authorize(httplib2.Http())

	# Build the Gmail service from discovery

    gmail_service = discovery.build('gmail', 'v1', http=http)

    message = gmail_service.users().messages().get(userId='me', id=msg_id, format='raw').execute()
    msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
    mime_msg = email.message_from_string(msg_str)
    print mime_msg
    return 'test'

@app.route("/v1/gmail/messages/results/<job_key>", methods=['GET'])
def get_results(job_key):
    job = Job.fetch(job_key, connection=conn)
    if job.is_finished:
        js = json.dumps(job.result)
        resp = Response(js, status=200, mimetype='application/json')
        return resp
    else:
        return "Nay!", 202

    
if __name__ == '__main__':
    app.config['SECRET_KEY'] = 'super secret key'
    app.debug = True
    app.run()
