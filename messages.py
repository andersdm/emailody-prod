# -*- coding: utf-8 -*-
from googleapiclient import discovery
from googleapiclient.http import BatchHttpRequest
from oauth2client import client
from rq import Queue
from rq.job import Job
from worker import conn

import httplib2
import re
import json

# Find the stack on which we want to store the database connection.
# Starting with Flask 0.9, the _app_ctx_stack is the correct one,
# before that we need to use the _request_ctx_stack.
#q = Queue(connection=conn)

def get_messages(pagenr,contact,credentials):
    messages=[]
    gmail_credentials = client.OAuth2Credentials.from_json(credentials)
    http = gmail_credentials.authorize(httplib2.Http())

# Build the Gmail service from discovery

    gmail_service = discovery.build('gmail', 'v1', http=http)
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
        
        messages.append(Contact)
            
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
    return messages
