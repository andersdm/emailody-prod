# -*- coding: utf-8 -*-
import os
import logging
import sys
import httplib2
import re
import json
from flask import Flask, abort, redirect, url_for, Response, render_template, session, request
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON
from rq import Queue
from rq.job import Job
from worker import conn
from googleapiclient import discovery
from googleapiclient.http import BatchHttpRequest
from oauth2client import client

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'memcached'
app.config['SECRET_KEY'] = 'super secret key'
app.debug = True
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)
app.config.from_object(os.environ['APP_SETTINGS'])
db = SQLAlchemy(app)

q = Queue(connection=conn)
from contacts import get_contacts

from models import *



@app.route('/')
def index():
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

    results = {}
    job = q.enqueue_call(func=get_contacts, args=(pagenr,session['seen'],session['credentials']), result_ttl=5000)
    return job.get_id()
    
    #return results
	#return render_template('index.html', results=results)
	

@app.route('/v1/gmail/messages/<int:msgnr>')
def messages(msgnr):
    if 'credentials' not in session:
        return redirect(url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    if credentials.access_token_expired:
        return redirect(url_for('oauth2callback'))

    if messages not in session:
        session['messages'] = []	

# Authorize the httplib2.Http object with our credentials

    http = credentials.authorize(httplib2.Http())

# Build the Gmail service from discovery

    gmail_service = discovery.build('gmail', 'v1', http=http)
    contact = session['seen'][msgnr]
    query = "\"to:'" + contact + "' AND from:me \" OR from:'" + contact + "'"
    message_ids = gmail_service.users().messages().list(userId='me',
            maxResults=10, labelIds='INBOX', q=query).execute()
    
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
        
        session['messages'].append(Contact)
            
    #for msg_id in message_ids['messages']:
    #    batchContacts.add(gmail_service.users().messages().get(userId='me',
    #              id=msg_id['id'], format='metadata',
    #              metadataHeaders=['from', 'date']))
    #batchContacts.execute()
    batchMails = BatchHttpRequest(callback=mailscallbackfunc)
    
    for msg_id in message_ids['messages']:
        batchMails.add(gmail_service.users().messages().get(userId='me',
                  id=msg_id['id'], format='metadata',
                  metadataHeaders=['from', 'date', 'subject']))
    batchMails.execute()
    
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

    js = json.dumps(session['messages'])
    resp = Response(js, status=200, mimetype='application/json')
    return job.get_id()

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

@app.route("/results/<job_key>", methods=['GET'])
def get_results(job_key):

    job = Job.fetch(job_key, connection=conn)

    if job.is_finished:
        session['seen'] = session['seen'] + job.result['seen']
        
        js = json.dumps(session['seen'])
        resp = Response(js, status=200, mimetype='application/json')
        return resp
    else:
        return "Nay!", 202

    
if __name__ == '__main__':
    app.config['SECRET_KEY'] = 'super secret key'
    app.debug = True
    app.run()
