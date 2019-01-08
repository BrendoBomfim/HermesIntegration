from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from apiclient.http import MediaFileUpload
import sys
from apiclient import errors

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/drive'


def upload_file(name, myme):
	store = file.Storage('token.json')
	creds = store.get()
	if not creds or creds.invalid:
		flow = client.flow_from_clientsecrets('auth/client_secret.json', SCOPES)
		creds = tools.run_flow(flow, store)
	service = build('drive', 'v3', http=creds.authorize(Http()))

	file_metadata = {'name': name,
						'writersCanShare': True}
	media = MediaFileUpload('files/' + name,
							mimetype=myme)
	files = service.files().create(body=file_metadata,
										media_body=media,
										fields='id, webContentLink').execute()
	
	return set_sharing_permission(files['id'], service)


def set_sharing_permission(file_id, service):
	new_permission = {
	'type': 'anyone',
	'role': 'reader'
	}

	try:
		return service.permissions().create(fileId=file_id, body=new_permission).execute()
	except :
		print ("Unexpected error:", sys.exc_info())
		return ''