# encoding=utf8
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import os
import logging
import sys
import httplib2
import re
import json
import redis
import urllib
import base64
import email
import uuid
from threading import Thread
from apiclient import errors
from flask import Markup
from flask import Flask, abort, redirect, url_for, Response, render_template, session, request
#from flask.ext.sqlalchemy import SQLAlchemy
#from sqlalchemy.dialects.postgresql import JSON
#from rq import Queue
#from rq.job import Job
#from worker import conn
redis_url = os.getenv('REDISCLOUD_URL', 'redis://localhost:6379')
conn = redis.StrictRedis.from_url(redis_url)
from googleapiclient import discovery
from googleapiclient.http import BatchHttpRequest
from oauth2client import client
from flask_kvsession import KVSessionExtension
from simplekv.memory.redisstore import RedisStore
store = RedisStore(conn)
app = Flask(__name__)
KVSessionExtension(store, app)
#app.config['SESSION_TYPE'] = 'memcached'
from messages import get_messages
app.config['SECRET_KEY'] = 'super secret key'
#app.debug = True
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)
#app.config.from_object(os.environ['APP_SETTINGS'])
#db = SQLAlchemy(app)

#q = Queue(connection=conn)
#from contacts import get_messages

#from models import *



@app.route('/')
def index():
    
    session['contactsNextPageToken'] = 0
    session['contacts'] = []
    session['seen'] = []
    session['mails'] = []
    session['messageIds'] = []
    session['maillist'] = []
    session['messagelist'] = []

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
    
    http = credentials.authorize(httplib2.Http(cache=".cache"))

# Build the Gmail service from discovery

    gmail_service = discovery.build('gmail', 'v1', http=http)
    while (len(session['seen'])+1 < pagenr*10):
        
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
                    From = From.replace('\"','')

                    Name = Name.replace('\"','')
                
                

            if From not in session['seen']:
                Contact = {
                    'id': len(session['seen']),
                    'date': Date,
                    'name': Name,
                    'address': Address,
                    'snippet': results['snippet'],
                    'unread': Unread
                    }
                session['contacts'].append(Contact)
                session['seen'].append(From)
        
        message_ids = gmail_service.users().messages().list(userId='me', maxResults=50, labelIds='INBOX', pageToken=session['contactsNextPageToken']).execute()
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
    return resp
	
@app.route('/v1/gmail/message/<msg_id>')
def get_message(msg_id):
    # Authorize the httplib2.Http object with our credentials	
    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    
    http = credentials.authorize(httplib2.Http(cache=".cache"))

# Build the Gmail service from discovery

    gmail_service = discovery.build('gmail', 'v1', http=http)

    try:
        message = gmail_service.users().messages().get(userId='me', id=msg_id,
                                             format='full').execute()
        
        message_payload = message['payload']
        

        if 'parts' in message_payload:
            message_parts = message_payload['parts']
            for part in message_parts:
                if part['mimeType'] == 'text/html':
                    message_body=part['body']
        else:
            message_body=message_payload['body']
            
        
        msg_str = base64.urlsafe_b64decode(message_body['data'].encode('utf-8'))
        

        #return msg_str
        #print 'Message snippet: %s' % message['snippet']
        #mime_msg = email.message_from_string(msg_str)
        #if mime_msg.is_multipart():
        #    for payload in mime_msg.get_payload():
            # if payload.is_multipart(): ...
        #        message = payload.get_payload()
        return msg_str
    
        #return message
    except errors.HttpError, error:
        print 'An error occurred: %s' % error

@app.route("/v1/gmail/messages/<int:contactId>/<int:pagenr>", methods=['GET'])
def get_messages(contactId,pagenr):
    contact = session['seen'][contactId]
    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    http = credentials.authorize(httplib2.Http(cache=".cache"))

# Build the Gmail service from discovery

    gmail_service = discovery.build('gmail', 'v1', http=http)
    def mailscallbackfunc(result, results, moreresults):
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
                if From == "Anders Damsgaard <andersdm@gmail.com>": #SKAL ÆNDRES
                    Sent = True
                else:
                    Sent = False
            if header['name'] == 'Subject':
                Subject = header['value']

        Contact = {
            'messageId': results['id'],
            'date': Date,
            'subject': Subject,
            'snippet': results['snippet'],
            'unread': Unread,
            'sent': Sent
            }

        mails.append(Contact)

    #for msg_id in message_ids['messages']:
    #    batchContacts.add(gmail_service.users().messages().get(userId='me',
    #              id=msg_id['id'], format='metadata',
    #              metadataHeaders=['from', 'date']))
    #batchContacts.execute()

    query = "\"to:'" + contact + "' AND from:me \" OR from:'" + contact + "'"
    message_ids = gmail_service.users().messages().list(userId='me',
            maxResults=10, labelIds='INBOX', q=query).execute()

    batchMails = BatchHttpRequest(callback=mailscallbackfunc)

    for msg_id in message_ids['messages']:
        batchMails.add(gmail_service.users().messages().get(userId='me',
                  id=msg_id['id'], format='metadata',
                  metadataHeaders=['from', 'date', 'subject']))
    batchMails.execute()
    js = json.dumps(session['mails'])
    resp = Response(js, status=200, mimetype='application/json')
    return resp


@app.route("/v1/gmail/listmessages", methods=['GET'])
def get_listmessages():
    def get_mailslist(message_ids, result, index, credentials):
        mails = []
        
        def mailscallbackfunc(result, results, moreresults):
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
                    if From == "Anders Damsgaard <andersdm@gmail.com>": #SKAL ÆNDRES
                        Sent = True
                    else:
                        Sent = False
                if header['name'] == 'Subject':
                    Subject = header['value']

            Contact = {
                'messageId': results['id'],
                'date': Date,
                'subject': Subject,
                'snippet': results['snippet'],
                'unread': Unread,
                'sent': Sent
                }

            mails.append(Contact)

        #for msg_id in message_ids['messages']:
        #    batchContacts.add(gmail_service.users().messages().get(userId='me',
        #              id=msg_id['id'], format='metadata',
        #              metadataHeaders=['from', 'date']))
        #batchContacts.execute()
        credentials = client.OAuth2Credentials.from_json(credentials)
        http = credentials.authorize(httplib2.Http(cache=".cache"))
        # Build the Gmail service from discovery
        gmail_service = discovery.build('gmail', 'v1', http=http)
        batchMails = BatchHttpRequest(callback=mailscallbackfunc)
        for msg_id in message_ids['messages']:
            batchMails.add(gmail_service.users().messages().get(userId='me',
                      id=msg_id['id'], format='metadata',
                      metadataHeaders=['from', 'date', 'subject']))
        batchMails.execute()
        results[index] = mails
        return True

    credentials = client.OAuth2Credentials.from_json(session['credentials'])

    http = credentials.authorize(httplib2.Http(cache=".cache"))
    # Build the Gmail service from discovery

    gmail_service = discovery.build('gmail', 'v1', http=http)
	
    def mailIdscallbackfunc(result, results, moreresults):
        session['messageIds'].append(results)

    batchMailIds = BatchHttpRequest(callback=mailIdscallbackfunc)
	
    for contact in session['seen']:
        query = "\"to:'" + contact + "' AND from:me \" OR from:'" + contact + "'"
        batchMailIds.add(gmail_service.users().messages().list(userId='me', maxResults=10, labelIds='INBOX', q=query))
    batchMailIds.execute()

    threads = [None]*len(session['seen'])
    results  = [None]*len(session['seen'])
    
    for i in range(0, 9):
        threads[i] = Thread(target=get_mailslist, args=(session['messageIds'][i], results, i, session['credentials']))
        threads[i].start()
                   
    for i in range(0, 9):
        threads[i].join()
                   
    js = json.dumps(results)
    resp = Response(js, status=200, mimetype='application/json')
    return resp



#if __name__ == '__main__':
#    app.config['SECRET_KEY'] = 'super secret key'
#    app.debug = True
#    app.run()
