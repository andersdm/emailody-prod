#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf8')
import httplib2
import re
import json
import redis
import base64
import datetime
from premailer import transform
from apiclient import errors
from flask import Flask, redirect, url_for, Response, render_template, session, request
from googleapiclient import discovery
from googleapiclient.http import BatchHttpRequest
from oauth2client import client
from flask_kvsession import KVSessionExtension
from simplekv.memory.redisstore import RedisStore
from fixbadunicode import fix_bad_unicode
from inlinestyler.utils import inline_css
redis_url = 'redis://rediscloud:u1ODHW41noA8sqMG@pub-redis-16921.us-east-1-4.6.ec2.redislabs.com:16921'
conn = redis.StrictRedis.from_url(redis_url)
store = RedisStore(conn)
app = Flask(__name__)
KVSessionExtension(store, app)
app.config['SECRET_KEY'] = 'super secret key'

@app.route('/')
def index():

    session['contactsNextPageToken'] = 0
    session['contacts'] = []
    session['seen'] = []
    session['mails'] = []
    session['maillist'] = []

    if 'credentials' not in session:
        return redirect(url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    if credentials.access_token_expired:
        return redirect(url_for('oauth2callback'))
    else:
        return render_template('index.html')


@app.route('/oauth2callback')
def oauth2callback():
    flow = client.flow_from_clientsecrets('/home/Andersdm/emailody/client_secrets.json'
            , scope='https://www.googleapis.com/auth/gmail.readonly',
            redirect_uri=url_for('oauth2callback', _external=True))
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
    http = credentials.authorize(httplib2.Http(cache='.cache'))

# Build the Gmail service from discovery

    gmail_service = discovery.build('gmail', 'v1', http=http)
    while len(session['seen']) + 1 < pagenr * 10:

# Retrieve a page of threads

# Print ID for each thread
# if threads['threads']:
#  for thread in threads['threads']:
#    print 'Thread ID: %s' % (thread['id'])

        def contactscallbackfunc(result, results, moreresults):
            if 'UNREAD' in results['labelIds']:
                Unread = True
            else:
                Unread = False
            for header in results['payload']['headers']:
                if header['name'].lower() == 'from':
                    From = header['value']
                    address = From.split()[-1]
                    address = re.sub(r'[<>]', '', address)
                    Address = address.strip()
                    Domain = Address.split('@')[1]
                    if Domain == 'facebookmail.com':
                        Domain = 'facebook.com'
                    Name = From.rsplit(' ', 1)[0]
                    From = From.replace('"', '')
                    Name = Name.replace('"', '')

            if From not in session['seen'] and Address != session['user_address']:
                Contact = {
                    'id': len(session['seen']),
                    'date': results['internalDate'],
                    'name': Name,
                    'initial': Name[0].upper(),
                    'address': Address,
                    'domain': Domain,
                    'snippet': results['snippet'],
                    'unread': Unread,
                    }
                session['contacts'].append(Contact)
                session['seen'].append(From)

        #query = ''

        #if not session['seen']:
        #    pass
        #else:
        #    query = 'from:('
        #    for From in session['seen']:
        #        query = query + "-'" + From + "', "
        #    query = query + ')'

        # query = "\"to:'" + contact + "' AND from:me \" OR from:'" + contact + "'"
        user_id = gmail_service.users().getProfile(userId='me').execute()
        session['user_address'] = user_id['emailAddress']
        message_ids = gmail_service.users().messages().list(userId='me'
                , maxResults=50,
                pageToken=session['contactsNextPageToken']).execute()
        batchContacts = BatchHttpRequest(callback=contactscallbackfunc)
        session['contactsNextPageToken'] = message_ids['nextPageToken']
        for msg_id in message_ids['messages']:
            batchContacts.add(gmail_service.users().messages().get(userId='me'
                              , id=msg_id['id'], format='metadata',
                              metadataHeaders=['from', 'date']))
        batchContacts.execute()

    if pagenr - 1 == 0:
        start = 0
        end = 10
    else:
        start = (pagenr - 1) * 10
        end = pagenr * 10
    response = {'nextPageToken': session['contactsNextPageToken'],
                'contacts': (session['contacts'])[start:end]}
    js = json.dumps(response)
    resp = Response(js, status=200, mimetype='application/json')
    return resp


@app.route('/v1/gmail/message/<msg_id>')
def get_message(msg_id):

    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    http = credentials.authorize(httplib2.Http(cache='.cache'))
    gmail_service = discovery.build('gmail', 'v1', http=http)

    try:
        message = gmail_service.users().messages().get(userId='me',
                id=msg_id, format='full').execute()
        message_payload = message['payload']

        if 'parts' in message_payload:
            for part in message_payload['parts']:
                if (part['mimeType'] == 'text/html') or (part['mimeType'] == 'text/plain'):
                    print "#0"
                    message_body = part['body']
                    for header in part['headers']:
                        if header['name'] == 'Content-Type':
                            charset = header['value'].rpartition('charset=')[2]
                            charset = re.sub('"', '', charset, flags=re.DOTALL)
                        if header['name'] == 'Content-Transfer-Encoding':
                            transferencoding = header['value']
                if 'parts' in part:
                    print "#1"
                    for part in part['parts']:
                        if (part['mimeType'] == 'text/html') or (part['mimeType'] == 'text/plain'):
                            message_body = part['body']
                            for header in part['headers']:
                                if header['name'] == 'Content-Type':
                                    charset = header['value'].rpartition('charset=')[2]
                                    charset = re.sub('"', '', charset, flags=re.DOTALL)
                                if header['name'] == 'Content-Transfer-Encoding':
                                    transferencoding = header['value']


            msg_str = base64.urlsafe_b64decode((message_body['data']).encode('ascii'))
#            msg_str = msg_str.decode(charset)
#            msg_str = msg_str.encode('utf-8')

        else:

            message_body = message_payload['body']
            print "#3"
            for header in message_payload['headers']:
                                if header['name'] == 'Content-Type':
                                    charset = header['value'].rpartition('charset=')[2]
                                    charset = re.sub('"', '', charset, flags=re.DOTALL)
            msg_str = base64.urlsafe_b64decode((message_body['data']).encode('ascii'))
#            msg_str = msg_str.encode('utf-8')
            msg_str = '<pre>' + msg_str + '</pre>'

        #print transferencoding
        #if transferencoding == 'quoted-printable':
        #    print "YEEEEEEEEP"
        #    msg_str = quopri.decodestring(msg_str)
        #if charset != 'UTF-8':
        #print charset
        #msg_str = msg_str.decode(charset, errors='ignore')
        msg_str = unicode(msg_str)
        msg_str = fix_bad_unicode(msg_str)
        #msg_str = msg_str.encode('utf-8', errors='ignore')
        #msg_str = msg_str.decode(charset)
        #msg_str = msg_str.encode('utf-8')

        #if charset.lower() is not 'utf-8':


        msg_str = re.sub('!important', '', msg_str, flags=re.DOTALL)

        try:
            transformed_msg = inline_css(msg_str)
        except:
            transformed_msg = msg_str #FIX mig

        clean_msg = re.sub('<html>', '', transformed_msg,
                           flags=re.DOTALL)
        clean_msg = re.sub('</html>', '', clean_msg, flags=re.DOTALL)
        clean_msg = re.sub('<head>.*?</head>', '', clean_msg,
                           flags=re.DOTALL)
        clean_msg = re.sub('<head>.*?</head>', '', clean_msg,
                           flags=re.DOTALL)
        clean_msg = clean_msg.replace('body', 'div', 1)
        clean_msg = re.sub('<body>', '', clean_msg, flags=re.DOTALL)
        clean_msg = re.sub('</body>', '', clean_msg, flags=re.DOTALL)
        clean_msg = re.sub('<style type="text/css">.*?</style>', '',
                           clean_msg, flags=re.DOTALL)
        clean_msg = re.sub('<style type="text/css">.*?</style>', '',
                           clean_msg, flags=re.DOTALL)

        return clean_msg
    except errors.HttpError, error:

        # return message

        print 'An error occurred: %s' % error


@app.route('/v1/gmail/messages/<int:contactId>', methods=['GET'])
def get_messages(contactId):
    contact = session['seen'][contactId]
    contact_address = contact.split()[-1]
    contact_address = re.sub(r'[<>]', '', contact_address)
    contact_address = contact_address.strip()
    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    http = credentials.authorize(httplib2.Http(cache='.cache'))

# Build the Gmail service from discovery

    gmail_service = discovery.build('gmail', 'v1', http=http)

    def mailscallbackfunc(result, results, moreresults):
        if 'labelIds' in results:
            if 'UNREAD' in results['labelIds']:
                Unread = True
            else:
                Unread = False
        else:
            Unread = None

        for header in results['payload']['headers']:
            #if header['name'].lower() == 'date':
            #    Date = header['value']
            if header['name'].lower() == 'from':
                From = header['value']
                from_address = From.split()[-1]
                from_address = re.sub(r'[<>]', '', from_address)
                from_address = from_address.strip()
                if from_address.lower() == session['user_address']:
                    Sent = True
                else:
                    Sent = False
            if header['name'].lower() == 'subject':
                Subject = header['value']
            #timestamp = int(results['internalDate']) / 1000
            #Date = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        try:
            Subject # does a exist in the current namespace
        except NameError:
            Subject = 'Unknown Subject' # nope

        #print(value.strftime('%Y-%m-%d %H:%M:%S'))

        Contact = {
            'messageId': results['id'],
            'date': results['internalDate'],
            'subject': Subject,
            'snippet': results['snippet'],
            'unread': Unread,
            'sent': Sent,
            }

        session['mails'].append(Contact)

    query = "(from:me to:" + contact_address + ") OR (from:" + contact + ")"
    print "#######query############"
    print query
    message_ids = gmail_service.users().messages().list(userId='me',
            maxResults=10, q=query).execute()
    #labelIds='INBOX',
    batchMails = BatchHttpRequest(callback=mailscallbackfunc)

    for msg_id in message_ids['messages']:
        batchMails.add(gmail_service.users().messages().get(userId='me'
                       , id=msg_id['id'], format='metadata',
                       metadataHeaders=['from', 'date', 'subject']))
    batchMails.execute()
    response = {'messages': session['mails']}
    js = json.dumps(response)
    resp = Response(js, status=200, mimetype='application/json')
    return resp