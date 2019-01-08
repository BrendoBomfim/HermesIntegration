#Python libraries that we need to import for our bot
import random
import base64
import requests
import time
import datetime as dt
from flask import Flask, request
from pymessenger.bot import Bot
import os
import upload_files
import json
from pymessenger.utils import AttrsEncoder

app = Flask(__name__)
#ACCESS_TOKEN = 'ACCESS_TOKEN'   
ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
#VERIFY_TOKEN = 'VERIFY_TOKEN'   
VERIFY_TOKEN = os.environ['VERIFY_TOKEN']
bot = Bot (ACCESS_TOKEN)

#We will receive messages that Facebook sends our bot at this endpoint 
@app.route("/", methods=['GET', 'POST'])
def receive_message():
	if request.method == 'GET':
		"""Before allowing people to message your bot, Facebook has implemented a verify token
		that confirms all requests that your bot receives came from Facebook.""" 
		token_sent = request.args.get("hub.verify_token")
		return verify_fb_token(token_sent)
	#if the request was not get, it must be POST and we can just proceed with sending a message back to user
	else:
	   # get whatever message a user sent the bot
		output = request.get_json()
		for event in output['entry']:
			messaging = event['messaging']
			for message in messaging:
				epoch_now = time.time()
				frmt_date = dt.datetime. utcfromtimestamp(epoch_now).strftime("%Y/%m/%d %H:%M")
				if message.get('message'):
					#Facebook Messenger ID for user so we know where to send response back to
					recipient_id = message['sender']['id']
					print(message)
					if message['message'].get('text'):
						payload = {'sender': message['sender']['id'], 'recipient': message['recipient']['id'],
							'send_date':frmt_date, 'content': message['message']['text'], 'message_id': message['message']['mid'], 'plataform_name': 'facebook'}
						send_omni_message(payload)
						
					#if user sends us a GIF, photo,video, or any other non-text item
					if message['message'].get('attachments'):
						for att in message['message'].get('attachments'):
							file_type = att['type']
							url_name = att['payload']['url']
							file_name = url_name.split("?")[0].split("/")[-1]
							file_location = "/tmp/" + file_name

							base64_string = download_file(url_name)
							#save_file(base64_string, file_location)

							payload = {'sender': message['sender']['id'], 'recipient': message['recipient']['id'],
								'send_date':frmt_date, 'media': 'media',
								'media_type': file_type, 'plataform_name': 'facebook',
								'media_name': file_name, 'content': base64_string,
								'message_id': message['message']['mid'] }

							send_omni_message(payload)

							#print(send_attachment_message(recipient_id, file_location, file_type ))

	return "Message Processed"

@app.route("/customer-id", methods=['GET'])
def customer_info():
	recipient_id = request.args.get("recipient_id")
	if recipient_id:	
		fields = ['id', 'name', 'profile_pic']
		return bot.get_user_info(recipient_id, fields)
	else:
		return "recipient_id not found"

@app.route("/message", methods=['POST'])
def on_omni_message():
	req_data = request.get_json()

	if "media" in req_data:
		file_location = "/tmp/" + req_data["media_name"]
		save_file(req_data["content"], file_location) 
		return send_attachment_message(req_data["recipient"], file_location, req_data["media_type"])
	else:
		return send_message(req_data["recipient"], req_data["content"].encode())


def verify_fb_token(token_sent):
	#take token sent by facebook and verify it matches the verify token you sent
	#if they match, allow the request, else return an error 
	if token_sent == VERIFY_TOKEN:
		return request.args.get("hub.challenge")
	return 'Invalid verification token'

def send_omni_message(payload):
	request_endpoint = os.environ['OMNI_LINK'] + ':' + os.environ['OMNI_PORT'] + '/api/message'
	response = requests.post(
		request_endpoint,
		data=json.dumps(payload, cls=AttrsEncoder),
		headers={'Content-Type': 'application/json'})
	result = response.json()
	return result

#uses PyMessenger to send response to user
def send_message(recipient_id, response):
	#sends user the text message provided via input response parameter
	return bot.send_text_message(recipient_id, response)

def send_attachment_url_message(recipient_id, file_type, url):
	#sends user the text message provided via input response parameter
	return bot.send_attachment_url(recipient_id, file_type, url)

def send_attachment_message(recipient_id, file_location, file_type):
	return bot.send_attachment(recipient_id, file_location, file_type)

def save_file(data, file_location):
	with open(file_location, "wb") as fh:
		fh.write(base64.decodebytes(data))

def download_file(url):
	return base64.b64encode(requests.get(url).content)

if __name__ == "__main__":
	app.run(host='0.0.0.0', ssl_context=('cert/fullchain.pem', 'cert/privkey.pem'))
