#!/usr/bin/python
import base64
import requests
import time
import datetime as dt
from flask import Flask, request
from pymessenger.bot import Bot
import upload_files
import json
import logging
import os

# Number used on Hermes
recipient = 558598063953
logs_path = os.getcwd() + '/logs/'
log_name = logs_path + str(recipient) + '_hermes_integration.log'
files_path = os.getcwd() + '/files/'

try:
    os.makedirs(logs_path)
except FileExistsError:
    pass

try:
    os.makedirs(files_path)
except FileExistsError:
    pass

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.DEBUG,
					filename=log_name, datefmt='%d/%m/%Y %H:%M:%S')
				
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Hermes credentials
api_username = "scio"
api_password = "Sc1o"
media_id = "f06e00c2-a552-49fe-995d-32a7b911dcac"

omni_link = "http://localhost"
omni_port = "3000"

bot = Bot(api_username, api_password)


@app.route("/", methods=['GET', 'POST'])
def receive_message():
	"""Receives messages from Hermes and send them to omni.

		Author:
			Brendo Bomfim

		Modification Date:
			07/03/2019
		
		Now send the status.

		Author:
			Brendo Bomfim

		Modification Date:
			15/05/2019

		Expects the JSON to be like:
		{
			"messages": [
				{
					"from": "1234567890",
					"id": "ABGGhSkIc2B_Ago-sDy5BNm1gI5",
					"text": {
						"body": "Hi"
					},
					"timestamp": "1529381066",
					"type": "text"
				}
			],
			"media_id": "xxx-xxx-xxxx"
		}
		Or
		{
			"media_id": "ffbff03b-d193-45ac-a28c-625568e9cd86",
			"contacts": {
				"status": "invalid",
				"msg_id": "644df3e9-dde5-4337-bed2-a4e73e7d39b6"
			}
		}
		Or
		[
			{
				"status": "delivered",
				"timestamp": "1557865064",
				"recipient_id": "558596361001",
				"id": "7318b99d-8813-45b1-a7ed-5cb4265da49b"
			}
		]

		Returns:
		  The sucess of error from omni request
	"""

	response = ""
	req_data = request.get_json()
	epoch_now = time.time()
	frmt_date = dt.datetime.utcfromtimestamp(epoch_now).strftime("%Y/%m/%d %H:%M")
	if req_data.get('messages'):
		messages = req_data["messages"]
		for message in messages:
			sender = message.get('from')

			if (len(sender) == 12):
				sender = sender[0:4] + '9' + sender[4:12]

			# For any media file, there is always going to be one of those
			if "image" in message or "voice" in message or "document" in message:
				file = message.get('image') or message.get('voice') or message.get('document')
				url_name = file.get('file')
				# Some files have ; for example: audio/ogg; codecs=opus
				extension = file.get('mime_type').split('/')[1].split(';')[0]
				file_name = url_name.split('/')[-1] + '.' + extension

				base64_string = download_file(url_name)

				payload = {'sender': sender, 'recipient': recipient,
						   'send_date': frmt_date, 'media': 'media',
						   'media_type': message.get('type'), 'plataform_name': 'whatsapp_business',
						   'media_name': file_name, 'content': base64_string,
						   'message_id': message.get('id')}

				logger.debug(f"receive_message -> message -> file -> payload: {payload}")

				response = send_omni_message(payload)

				logger.debug(f"receive_message -> message -> file -> response: {response}" )

			elif "text" in message:
				payload = {'sender': sender, 'recipient': recipient,
						   'send_date': frmt_date, 'content': message.get('text').get('body'),
						   'message_id': message.get('id'), 'plataform_name': 'whatsapp_business'}

				logger.debug(f"receive_message -> message -> text -> payload: {payload}")

				response = send_omni_message(payload)

				logger.debug(f"receive_message -> message -> file -> response: {response}")

	elif "statuses" in req_data:
		statuses = req_data["statuses"]
		for status in statuses:
			payload = {'status': status.get('status'), 'id': status.get('id')}

			logger.debug(f"receive_message -> message -> statuses -> payload: {payload}")

			response = send_omni_status(payload)

			logger.debug(f"receive_message -> message -> statuses -> response: {response}")

	elif "media_id" in req_data:
		payload = {'status': req_data.get('contacts').get('status'), 'id': req_data.get('contacts').get('msg_id')}

		logger.debug(f"receive_message -> message -> media_id -> payload: {payload}")

		response = send_omni_status(payload)

		logger.debug(f"receive_message -> message -> media_id -> response: {response}")
		
	else:
		logger.info("Not handled")
		logger.info(req_data)
	return response


@app.route("/message", methods=['POST'])
def on_omni_message():
	"""Receives messages from Omni and uses the appropriate method to send them to Hermes.

			Author:
				Brendo Bomfim

			Modification Date:
				07/03/2019

			Expects the JSON to be like:
			{
				"recipient": "+5585996361001",
				"type": "text",
				"content": "olar"
			}

			Returns:
			  The sucess of error from omni request
		"""
	req_data = request.get_json()

	if req_data.get('media_type'):
		return send_attachment_message(req_data)
	elif req_data.get('message'):
		return send_hsm_message(req_data)
	else:
		return send_text_message(req_data)


@app.route("/create_hsm", methods=['POST'])
def on_create_hsm():
	"""Creates a HSM to send them to Hermes.

				Author:
					Brendo Bomfim

				Modification Date:
					07/03/2019

	"""
	req_data = request.get_json()
	return create_hsm(req_data["hsm_name"], req_data["hsm_message"])


def send_omni_message(payload):
	"""Sends the payload to Omni.

					Author:
						Brendo Bomfim

					Modification Date:
						07/03/2019

					Changed the route.
					Author:
						Brendo Bomfim
					Modification Date:
						24/05/2019

					Args:
						payload: the message to be sendo to omni. e.g:
						{
							"sender": "5585996361064",
							"recipient": 558588886522,
							"send_date": "2019/03/05 13:15",
							"content": "Hello",
							"message_id": "5585996361064s",
							"plataform_name": "whatsapp_business"
						}
					Returns:
					  The sucess of error from the request made to omni
		"""
	request_endpoint = omni_link + ':' + omni_port + '/api/message/active'
	response = requests.post(
		request_endpoint,
		data=json.dumps(payload),
		headers={'Content-Type': 'application/json'})
	return response.content

def send_omni_status(payload):
	"""Sends the status payload to Omni.

					Author:
						Brendo Bomfim

					Modification Date:
						15/05/2019

					Args:
						payload: the message to be sendo to omni. e.g:
						{
							"status": "invalid",
							"id": 644df3e9-dde5-4337-bed2-a4e73e7d39b6
							
						}
					Returns:
					  The sucess of error from the request made to omni
		"""
	request_endpoint = omni_link + ':' + omni_port + '/dialer/status'
	response = requests.post(
		request_endpoint,
		data=json.dumps(payload),
		headers={'Content-Type': 'application/json'})
	return response.content


def send_text_message(omni_message):
	message = json.loads('{}')
	message["message"] = {}
	message["message"].update({"to": format_phone(omni_message["recipient"]),
							   "type": "text",
							   "text": omni_message["content"],
							   "media_id": media_id,
							   "recipient_type": "individual"})

	logger.debug(f"send_text_message -> message: {message}")

	response = bot.send_raw(message)

	logger.debug(f"send_text_message -> response: {response}")

	return response


def send_hsm_message(omni_message):
	# message = json.loads('{}')
	# message["message"] = {}
	# message["message"].update({"to": format_phone(omni_message["recipient"]),
	#                            "type": omni_message["media_type"],
	# 						   "media_id": media_id,
	# 						   "hsm": omni_message["hsm"],
	#                            "recipient_type": "individual"})
	#
	# logger.debug(f"send_hsm_message -> message: {message}")

	response = bot.send_raw(omni_message)

	logger.debug(f"send_hsm_message -> response: {response}")

	return response


def send_attachment_message(omni_message):
	message = json.loads('{}')
	message["message"] = {}
	type = get_type(omni_message["media_type"])
	# Save the file locally before uploading and return the path to the file
	path = upload_files.save_get_file(omni_message["content"], omni_message["media_name"])
	# Uses the path to make a upload on google drive and gets the public utl
	url = upload_files.upload_file(path, omni_message["media_type"])

	message["message"].update({"to": format_phone(omni_message["recipient"]),
							   "type": type,
							   "content_type": omni_message["media_type"],
							   "media_id": media_id,
							   "url": url,
							   "caption": omni_message["media_name"],
							   "recipient_type": "individual"})
	if "caption" in omni_message:
		message["message"].update({"caption": omni_message["caption"]})

	logger.debug(f"send_attachment_message -> message: {message}")

	response = bot.send_raw(message)

	logger.debug(f"send_attachment_message -> response: {response}")

	return response


def get_type(myme):
	type = myme.split('/')[0]
	if type != "image" or type != "audio":
		return "document"
	else:
		return type


def format_phone(phone_number):
	return "+" + phone_number


def save_file(data, file_location):
	with open(file_location, "wb") as fh:
		fh.write(base64.decodebytes(data))


def download_file(url):
	return base64.b64encode(requests.get(url).content).decode("utf-8")


def create_hsm(hsm_name, hsm_message):
	return bot.create_hsm(hsm_name, hsm_message)


if __name__ == "__main__":
	app.run(threaded=True, host='0.0.0.0')
