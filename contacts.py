from googleapiclient import discovery
from googleapiclient.http import BatchHttpRequest
from oauth2client import client
import httplib2
import re
import json
# Find the stack on which we want to store the database connection.
# Starting with Flask 0.9, the _app_ctx_stack is the correct one,
# before that we need to use the _request_ctx_stack.

def get_contacts(pagenr, seen, credentials):

# Authorize the httplib2.Http object with our credentials
    mails = []
    
    credentials = client.OAuth2Credentials.from_json(credentials)
    
    
    http = credentials.authorize(httplib2.Http())

# Build the Gmail service from discovery

    gmail_service = discovery.build('gmail', 'v1', http=http)

# Retrieve a page of threads

    message_ids = gmail_service.users().messages().list(userId='me',
                maxResults=20, labelIds='INBOX').execute()

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
                
                

        if From not in seen:
            Contact = {
                'messageId': results['id'],
                'contactNr': len(seen),
                'date': Date,
                'name': Name,
                'address': Address,
                'snippet': results['snippet'],
                'unread': Unread,
                }
            mails.append(Contact)
            seen.append(From)
   
    batchContacts = BatchHttpRequest(callback=contactscallbackfunc)
    for msg_id in message_ids['messages']:
        batchContacts.add(gmail_service.users().messages().get(userId='me',
                  id=msg_id['id'], format='metadata',
                  metadataHeaders=['from', 'date']))
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
    resp = {'mails': mails, 'seen': seen}
    return resp
