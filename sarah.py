import requests
import time
import os
import pyttsx3
import winsound


class Asset:
	def __init__(self, tower, floor, is_cart):
		self.tower = tower
		self.floor = floor
		self.is_cart = is_cart

class Ticket:
	def __init__(self, summary, asset = None):
		self.asset = asset
		self.summary = summary

class Remedy:
	def __init__(self):
		# Set the cookies
		self.base_url = 'https://remsmartitvp.ynhh.org:8443/ux/smart-it/#/ticket-console'
		self.session_properties = {
		'JSESSIONID': 'AB68EEADA7B1FBBD40F96E1491788638',
		'NSC_wtsw_sfntnbsujuwq_8443_ofx':'ffffffff0927ae1b45525d5f4f58455e445a4a421518'
		}
		# Set payload
		self.payload = {"filterCriteria":{"assignedSupportGroups":[{"name":"Desktop Support - BH","company":{"name":"Yale New Haven Health"},"organization":"IT Support","isDefault":True,"id":"SGP000000000184"}],"statusMappings":["open"],"ticketTypes":["incident"]},"chunkInfo":{"startIndex":0,"chunkSize":75},"sortInfo":{},"attributeNames":["priority","id","assignee","summary","status","submitDate"],"customAttributeNames":[]}

		self.ticket_url = 'https://remsmartitvp.ynhh.org:8443/ux/rest/v2/person/workitems/get'

	def get_floor_url(self, computer_id):
		return f'https://remsmartitvp.ynhh.org:8443/ux/rest/v2/incident/{computer_id}'

	def get_asset_info(self, asset_name):
		if asset_name:
			asset_name = asset_name.strip() # Remove any spaces
			if len(asset_name) != 15:
				return None

			tower = self.towers[asset_name[1 : 3]]
			floor = str(int(asset_name[4 : 6]))
			is_cart = 'CWM' in asset_name

			return Asset(tower, floor, is_cart)
		else:
			return None

class Sarah:
	def __init__(self):
		# Define her voice
		self.voice_engine = pyttsx3.init()
		self.voice_id = "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0"
		self.voice_engine.setProperty('voice', self.voice_id)
		self.voice_engine.setProperty('rate', 155)
		self.voice_engine.setProperty('volume', 2)

		# Start remedy
		self.remedy = Remedy()

		# Define tickets
		self.tickets = []

		# Look for tickets
		self.speak("Searching tickets")
		self.start()

	def get_asset_name(self, session, computer_id):
		# Returns the computer name if one
		data = session.get(self.remedy.get_floor_url(computer_id), cookies=self.remedy.session_properties)
		data = data.json()
		data = data[0]['items'][0]
		data = data['desc']

		if 'Asset ID:' in data:
			asset_id = data.index('Asset ID:')
			index = len('Asset ID:') + asset_id
			computer_name = data[index : index + 15].strip()
			return computer_name
		else:
			return False
		
	def get_tickets(self, s):
		data = s.post(self.remedy.ticket_url, cookies=self.remedy.session_properties, 
				json=self.remedy.payload)

		if data.status_code == 200:

			tickets = data.json()
			tickets = tickets[0]['items'][0]['objects']

			# Handle reading the tickets
			if len(self.tickets) != 0:
				for t in tickets:
					if not t['id'] in self.tickets:
						summary = t['summary']
						new_ticket = Ticket(summary, self.remedy.get_asset_info(self.get_asset_name(s, t['id'])))
						self.alert()
						if new_ticket.asset:
							cart_msg = "...This is a cart" if new_ticket.asset.is_cart else "...This is a PC"
							self.speak(f"New ticket...Located at {new_ticket.asset.tower} {new_ticket.asset.floor}{cart_msg}...{new_ticket.summary}")
						else:
							self.speak(f"New ticket...{new_ticket.summary}")

			for t in tickets:
				_id = t['id']
				_type = t['type']
				summary = t['summary']

				if not _id in self.tickets:
					self.tickets.append(t['id'])

				print(_id, _type, summary)


	def start(self):
		with requests.Session() as s:
			while True:
				try:
					self.get_tickets(s)
					time.sleep(10)
					os.system('cls')	

				except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
					self.speak("I was disconnected from the server, trying to re-connect")
					self.connect_server(s)

				except Exception as e:
					self.speak("Unknown error, look at the logs for details.")
					print(e)
					exit()

	def speak(self, msg):
		self.voice_engine.say(msg)
		self.voice_engine.runAndWait()

	def alert(self):
		winsound.PlaySound('alert.wav', winsound.SND_FILENAME)

	def connect_server(self, s):
		# This will handle disconnects and re-connects
		for _ in range(10):
			try:
				response = s.get(self.remedy.base_url)
				self.speak("Re-connected to server")
				break

			except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
				print(f"Error: Disconnected, connection attempts left: {_}")
				time.sleep(3)
		else:
			self.speak("Could not establish a connection, ending session")
			exit()

if __name__ == '__main__':
	print("Log: Connecting to server..")
	Sarah()
