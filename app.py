# -*- coding: utf-8 -*-
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
        #message = 'PCFET0NUWVBFIGh0bWwgUFVCTElDICItLy9XM0MvL0RURCBIVE1MIDQuMCBUcmFuc2l0aW9uYWwvL0VOIiAiaHR0cDovL3d3dy53My5vcmcvVFIvUkVDLWh0bWw0MC9sb29zZS5kdGQiPg0KPGh0bWwgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkveGh0bWwiPjxoZWFkPjxtZXRhIGNvbnRlbnQ9InRleHQvaHRtbDsgY2hhcnNldD11dGYtOCIgaHR0cC1lcXVpdj0iQ29udGVudC1UeXBlIj48c3R5bGU-DQogICAgICAgIEBmb250LWZhY2Ugew0KICAgICAgICAgICAgZm9udC1mYW1pbHk6ICJwcm94aW1hX25vdmEiOw0KICAgICAgICAgICAgc3JjOiB1cmwoImh0dHBzOi8vd3d3LmRyb3Bib3guY29tL3N0YXRpYy9mb250cy9wcm94aW1hbm92YS9wcm94aW1hLW5vdmEtcmVndWxhci5vdGYiKSBmb3JtYXQoIm9wZW50eXBlIik7DQogICAgICAgICAgICBmb250LXdlaWdodDogbm9ybWFsOw0KICAgICAgICAgICAgZm9udC1zdHlsZTogbm9ybWFsOw0KICAgICAgICB9DQogICAgICAgIGEgew0KICAgICAgICAgICAgY29sb3I6ICMwMDdlZTY7DQogICAgICAgICAgICB0ZXh0LWRlY29yYXRpb246IG5vbmU7DQogICAgICAgIH0NCiAgICAgICAgPC9zdHlsZT48L2hlYWQ-PGJvZHkgc3R5bGU9InBhZGRpbmc6IDA7IHdpZHRoOiAxMDAlICFpbXBvcnRhbnQ7IC13ZWJraXQtdGV4dC1zaXplLWFkanVzdDogMTAwJTsgbWFyZ2luOiAwOyAtbXMtdGV4dC1zaXplLWFkanVzdDogMTAwJTsiIG1hcmdpbmhlaWdodD0iMCIgbWFyZ2lud2lkdGg9IjAiPjxjZW50ZXI-PHRhYmxlIGNlbGxwYWRkaW5nPSI4IiBjZWxsc3BhY2luZz0iMCIgc3R5bGU9Iip3aWR0aDogNTQwcHg7IHBhZGRpbmc6IDA7IHdpZHRoOiAxMDAlICFpbXBvcnRhbnQ7IGJhY2tncm91bmQ6ICNmZmZmZmY7IG1hcmdpbjogMDsgYmFja2dyb3VuZC1jb2xvcjogI2ZmZmZmZjsiIGJvcmRlcj0iMCI-PHRyPjx0ZCB2YWxpZ249InRvcCI-DQo8dGFibGUgY2VsbHBhZGRpbmc9IjAiIGNlbGxzcGFjaW5nPSIwIiBzdHlsZT0iYm9yZGVyLXJhZGl1czogNHB4OyAtd2Via2l0LWJvcmRlci1yYWRpdXM6IDRweDsgYm9yZGVyOiAxcHggI2RjZWFmNSBzb2xpZDsgLW1vei1ib3JkZXItcmFkaXVzOiA0cHg7IiBib3JkZXI9IjAiIGFsaWduPSJjZW50ZXIiPjx0cj48dGQgY29sc3Bhbj0iMyIgaGVpZ2h0PSI2Ij48L3RkPjwvdHI-PHRyIHN0eWxlPSJsaW5lLWhlaWdodDogMHB4OyI-PHRkIHdpZHRoPSIxMDAlIiBzdHlsZT0iZm9udC1zaXplOiAwcHg7IiBhbGlnbj0iY2VudGVyIiBoZWlnaHQ9IjEiPjxpbWcgd2lkdGg9IjQwcHgiIHN0eWxlPSJtYXgtaGVpZ2h0OiA3M3B4OyB3aWR0aDogNDBweDsgKndpZHRoOiA0MHB4OyAqaGVpZ2h0OiA3M3B4OyIgYWx0PSIiIHNyYz0iaHR0cHM6Ly93d3cuZHJvcGJveC5jb20vc3RhdGljL2ltYWdlcy9lbWFpbHMvZ2x5cGgvZ2x5cGhfMzRAMngucG5nIj48L3RkPjwvdHI-PHRyPjx0ZD48dGFibGUgY2VsbHBhZGRpbmc9IjAiIGNlbGxzcGFjaW5nPSIwIiBzdHlsZT0ibGluZS1oZWlnaHQ6IDI1cHg7IiBib3JkZXI9IjAiIGFsaWduPSJjZW50ZXIiPjx0cj48dGQgY29sc3Bhbj0iMyIgaGVpZ2h0PSIzMCI-PC90ZD48L3RyPjx0cj48dGQgd2lkdGg9IjM2Ij48L3RkPg0KPHRkIHdpZHRoPSI0NTQiIGFsaWduPSJsZWZ0IiBzdHlsZT0iY29sb3I6ICM0NDQ0NDQ7IGJvcmRlci1jb2xsYXBzZTogY29sbGFwc2U7IGZvbnQtc2l6ZTogMTFwdDsgZm9udC1mYW1pbHk6IHByb3hpbWFfbm92YSwgJ09wZW4gU2FucycsICdMdWNpZGEgR3JhbmRlJywgJ1NlZ29lIFVJJywgQXJpYWwsIFZlcmRhbmEsICdMdWNpZGEgU2FucyBVbmljb2RlJywgVGFob21hLCAnU2FucyBTZXJpZic7IG1heC13aWR0aDogNDU0cHg7IiB2YWxpZ249InRvcCI-SGkgQW5kZXJzLDxicj48YnI-RGlkIHlvdSBrbm93IHRoYXQgaXQncyBlYXN5IHRvIGdldCBtb3JlIHNwYWNlIGZvciB5b3VyIERyb3Bib3g_PGJyPjxicj48Y2VudGVyPjxhIHN0eWxlPSJib3JkZXItcmFkaXVzOiAzcHg7IGZvbnQtc2l6ZTogMTVweDsgY29sb3I6IHdoaXRlOyBib3JkZXI6IDFweCAjMTM3M2I1IHNvbGlkOyBib3gtc2hhZG93OiBpbnNldCAwIDFweCAwICM2ZGIzZTYsIGluc2V0IDFweCAwIDAgIzQ4YTFlMjsgdGV4dC1kZWNvcmF0aW9uOiBub25lOyBwYWRkaW5nOiAxNHB4IDdweCAxNHB4IDdweDsgd2lkdGg6IDIzMHB4OyBtYXgtd2lkdGg6IDIzMHB4OyBmb250LWZhbWlseTogcHJveGltYV9ub3ZhLCAnT3BlbiBTYW5zJywgJ2x1Y2lkYSBncmFuZGUnLCAnU2Vnb2UgVUknLCBhcmlhbCwgdmVyZGFuYSwgJ2x1Y2lkYSBzYW5zIHVuaWNvZGUnLCB0YWhvbWEsIHNhbnMtc2VyaWY7IG1hcmdpbjogNnB4IGF1dG87IGRpc3BsYXk6IGJsb2NrOyBiYWNrZ3JvdW5kLWNvbG9yOiAjMDA3ZWU2OyB0ZXh0LWFsaWduOiBjZW50ZXI7IiBocmVmPSJodHRwczovL3d3dy5kcm9wYm94LmNvbS9sL2M5ZW92czNxVks1R0RkUkZpbWJUTkkvcHJpY2luZyI-VXBncmFkZSB5b3VyIERyb3Bib3g8L2E-PC9jZW50ZXI-DQo8YnI-V2hlbiB5b3UgdXBncmFkZSB5b3VyIERyb3Bib3gsIHlvdSBjYW46PGJyPjx1bCBzdHlsZT0ibWFyZ2luLXRvcDogMHB4OyBtYXJnaW4tYm90dG9tOiAwcHg7Ij48bGk-DQo8Yj5QdXQgZXZlcnl0aGluZyBpbiBEcm9wYm94PC9iPiB3aXRoIDEgVEIgKDEsMDAwIEdCKSBvZiBzcGFjZSBmb3IgeW91ciBwaG90b3MsIHZpZGVvcywgZG9jcywgYW5kIG90aGVyIGZpbGVzPC9saT4NCjxsaT4NCjxiPlByb3RlY3QgdGhlIHN0dWZmIHlvdSBzaGFyZTwvYj4gYnkgYWRkaW5nIHBhc3N3b3JkcyBhbmQgZXhwaXJhdGlvbnMgdG8gc2hhcmVkIGxpbmtzPC9saT4NCjxsaT4NCjxiPlNpbXBsaWZ5IGNvbGxhYm9yYXRpb248L2I-IHdpdGggdmlldy1vbmx5IHBlcm1pc3Npb25zIGZvciBzaGFyZWQgZm9sZGVyczwvbGk-DQo8bGk-DQo8Yj5LZWVwIHlvdXIgc3R1ZmYgc2FmZTwvYj4gd2l0aCByZW1vdGUgd2lwZSBmb3IgbG9zdCBkZXZpY2VzPC9saT4NCjwvdWw-PGJyPkhhcHB5IERyb3Bib3hpbmchPGJyPi0gVGhlIERyb3Bib3ggVGVhbTwvdGQ-DQo8dGQgd2lkdGg9IjM2Ij48L3RkPg0KPC90cj48dHI-PHRkIGNvbHNwYW49IjMiIGhlaWdodD0iMzYiPjwvdGQ-PC90cj48L3RhYmxlPjwvdGQ-PC90cj48L3RhYmxlPjx0YWJsZSBjZWxscGFkZGluZz0iMCIgY2VsbHNwYWNpbmc9IjAiIGFsaWduPSJjZW50ZXIiIGJvcmRlcj0iMCI-PHRyPjx0ZCBoZWlnaHQ9IjEwIj48L3RkPjwvdHI-PHRyPjx0ZCBzdHlsZT0icGFkZGluZzogMDsgYm9yZGVyLWNvbGxhcHNlOiBjb2xsYXBzZTsiPjx0YWJsZSBjZWxscGFkZGluZz0iMCIgY2VsbHNwYWNpbmc9IjAiIGFsaWduPSJjZW50ZXIiIGJvcmRlcj0iMCI-PHRyIHN0eWxlPSJjb2xvcjogI2E4YjljNjsgZm9udC1zaXplOiAxMXB4OyBmb250LWZhbWlseTogcHJveGltYV9ub3ZhLCAnT3BlbiBTYW5zJywgJ0x1Y2lkYSBHcmFuZGUnLCAnU2Vnb2UgVUknLCBBcmlhbCwgVmVyZGFuYSwgJ0x1Y2lkYSBTYW5zIFVuaWNvZGUnLCBUYWhvbWEsICdTYW5zIFNlcmlmJzsgLXdlYmtpdC10ZXh0LXNpemUtYWRqdXN0OiBub25lOyI-PHRkIHdpZHRoPSI0MDAiIGFsaWduPSJsZWZ0Ij5JZiB5b3UgcHJlZmVyIG5vdCB0byByZWNlaXZlIHRoZXNlIHRpcHMgZnJvbSBEcm9wYm94LCBwbGVhc2UgZ28gPGEgaHJlZj0iaHR0cHM6Ly93d3cuZHJvcGJveC5jb20vbC8xb3QyMHRnWDdBb1VYSkxqMjk5UDBCIj5oZXJlPC9hPi48YnI-RHJvcGJveCwgSW5jLiwgUE8gQm94IDc3NzY3LCBTYW4gRnJhbmNpc2NvLCBDQSA5NDEwNzwvdGQ-DQo8dGQgd2lkdGg9IjEyOCIgYWxpZ249InJpZ2h0Ij4mIzE2OTsgMjAxNSBEcm9wYm94PC90ZD4NCjwvdHI-PC90YWJsZT48L3RkPjwvdHI-PC90YWJsZT48L3RkPjwvdHI-PC90YWJsZT48L2NlbnRlcj48L2JvZHk-PC9odG1sPjxpbWcgd2lkdGg9IjEiIHNyYz0iaHR0cHM6Ly93d3cuZHJvcGJveC5jb20vbC9xQmNYeHM2d0RxVnJqSFcxenpkWEFRIiBoZWlnaHQ9IjEiIC8-'
        
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
        
        session['mails'].append(Contact)
            
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

    
#if __name__ == '__main__':
#    app.config['SECRET_KEY'] = 'super secret key'
#    app.debug = True
#    app.run()
