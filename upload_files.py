from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from apiclient.http import MediaFileUpload
import sys
import base64
import os
import logging

logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/drive'


def upload_file(location, myme):
	store = file.Storage('token.json')
	creds = store.get()
	if not creds or creds.invalid:
		flow = client.flow_from_clientsecrets('auth/client_secret.json', SCOPES)
		creds = tools.run_flow(flow, store)
	service = build('drive', 'v3', http=creds.authorize(Http()))

	folder_id = '1COr7rVjTkM1X778Fv-lU55PQvH9mDRKN'
	name = location.split("/")[-1]
	file_metadata = {
		'name': name,
		'parents': [folder_id],
		'writersCanShare': True
	}
	media = MediaFileUpload(location,
							mimetype=myme,
	                        resumable=True)
	files = service.files().create(body=file_metadata,
										media_body=media,
										fields='id, webContentLink').execute()

	return set_sharing_permission(files, service)


def set_sharing_permission(files, service):
	new_permission = {
	'type': 'anyone',
	'role': 'reader'
	}

	try:
		service.permissions().create(fileId=files['id'], body=new_permission).execute()
		return files['webContentLink']
	except :
		logger.error("Unexpected error: ", sys.exc_info())
		return ''


def save_get_file(file, file_name):
	file_data = base64.b64decode(file)
	try:
		save_path = os.getcwd() + '/files/'
		complete_name = os.path.join(save_path, file_name)

		f = open(complete_name, 'wb')
		f.write(file_data)
		f.close()

	except:
		logger.error("Unexpected error: ", sys.exc_info()[0])
		raise

	return complete_name