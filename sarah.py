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

class Remedy:
	def __init__(self):
		self.towers = {
			'ET' : 'East Tower',
			'WT' : 'West Tower',
			'NE' : 'North East',
			'NW' : 'North West',
			'PO' : 'Podium'
		}
		self.session_properties = {
			"JSESSIONID" : "AB68EEADA7B1FBBD40F96E1491788638",
			"NSC_wtsw_sfntnbsujuwq_8443_ofx" : "ffffffff0927ae1b45525d5f4f58455e445a4a421518"
		}
		# Set payload
		self.payload = {"filterCriteria":{"assignedSupportGroups":[{"name":"Desktop Support - BH","company":{"name":"Yale New Haven Health"},
		"organization":"IT Support","isDefault":True,"id":"SGP000000000184"}],"statusMappings":["open"],"ticketTypes":["incident"]},
		"chunkInfo":{"startIndex":0,"chunkSize":75},"sortInfo":{},"attributeNames":["priority","id","assignee","summary","status","submitDate"],
		"customAttributeNames":[]}

		self.ticket_url = 'https://remsmartitvp.ynhh.org:8443/ux/rest/v2/person/workitems/get'

	def get_desc(self, computer_id):
		return f'https://remsmartitvp.ynhh.org:8443/ux/rest/v2/incident/{computer_id}'

	def get_asset(self, name):
		tower = self.towers[name[1 : 3]]
		floor = str(int(name[4 : 6]))
		is_cart = 'CWM' in name

		return Asset(tower, floor, is_cart)

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
		data = session.get(self.remedy.get_desc(computer_id), cookies=self.remedy.session_properties)
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

	def new_ticket(ticket_id, ticket_summary):
		msg = "New ticket..."
		computer_name = self.get_asset_name(s, ticket_id)
		if computer_name:
			asset = self.remedy.get_asset(computer_name)
			cart_msg = "...This is a cart" if asset.is_cart else "...This is a PC"
			msg += f"Located at {asset.tower} {asset.floor}{cart_msg}...{ticket_summary}"
		else:
			msg += ticket_summary
			
		self.alert()
		self.speak(msg)
		
	def get_tickets(self, s):
		data = s.post(self.remedy.ticket_url, cookies=self.remedy.session_properties, 
				json=self.remedy.payload)

		tickets = data.json()
		tickets = tickets[0]['items'][0]['objects']

		# This adds tickets to the list
		for ticket in tickets:
			ticket_id = ticket['id']
			ticket_summary = ticket['summary']
			ticket_type = ticket['type']

			if not ticket_id in self.tickets:
				# We always want to skip the first batch
				if len(self.tickets == 0):
					skip = True

				if not skip:
					self.new_ticket(ticket_id, ticket_summary)
				self.tickets.append(ticket_id)

			print(ticket_id, ticket_type, ticket_summary)

		skip = False # Dirty

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
		for _ in range(20):
			try:
				response = s.get(self.remedy.ticket_url)
				self.speak("Re-connected to server")
				break

			except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
				print(f"Error: Disconnected, connection attempts made: {_}")
				time.sleep(3)
		else:
			self.speak("Could not establish a connection, ending session")
			exit()

if __name__ == '__main__':
	print("Log: Connecting to server..")
	Sarah()
