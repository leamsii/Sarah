import requests
import time
import os
import pyttsx3
import winsound

# Requests and pyttsx3 are both dependencies


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
			'PO' : 'Podium',
			'PT' : 'E-D',
			'RY' : 'Perry'
		}
		self.ticket_url = 'https://remsmartitvp.ynhh.org:8443/ux/rest/v2/person/workitems/get'
		# Set payload
		self.payload = {"filterCriteria":{"assignedSupportGroups":[{"name":"Desktop Support - BH","company":{"name":"Yale New Haven Health"},
		"organization":"IT Support","isDefault":True,"id":"SGP000000000184"}],"statusMappings":["open"],
		"ticketTypes":["incident"]},"chunkInfo":{"startIndex":0,"chunkSize":75},"sortInfo":{},
		"attributeNames":["priority","id","assignee","summary","status","submitDate"],"customAttributeNames":[]}

	def get_desc(self, computer_id):
		return f'https://remsmartitvp.ynhh.org:8443/ux/rest/v2/incident/{computer_id}'

	def get_asset(self, name):
		tower = self.towers[name[1 : 3]]
		try:
			floor = str(int(name[4 : 6]))
		except:
			floor = ''
			pass
			
		is_cart = 'CWM' in name

		return Asset(tower, floor, is_cart)

	def login(self, session):
		# Handle login into Remedy
		username = input("Username: ").strip()
		password = input("Password: ").strip()

		login_url = f'https://remsmartitvp.ynhh.org:8443/ux/rest/users/sessions/{username}'
		payload = {"password": password,"appName":"Galileo","appVersion":"2.0.00.000","apiVersion":1600000,"locale":"en","deviceToken":"dummyToken","os":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36","model":"Web Client"}

		r = session.post(login_url, cookies=self.session_properties, json=payload)

		if(r.status_code == 200):
			print("Log: Login successs!")
			os.system("cls")
		else:
			print("Error: Invalid credentials!")
			exit()

class Sarah:
	def __init__(self):
		# Define her voice
		self.voice_engine = pyttsx3.init()
		self.voice_id = "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0"
		self.voice_engine.setProperty('voice', self.voice_id)
		self.voice_engine.setProperty('rate', 160)
		self.voice_engine.setProperty('volume', 2)

		# Start remedy
		self.remedy = Remedy()

		# Define tickets
		self.tickets = []

		# Look for tickets
		self.speak("Searching tickets")
		self.session = requests.session()
		self.start()

	def get_session(self):
		# This will create a new session and get the cookies/session ID
		self.session = requests.session()
		data = self.session.get(self.remedy.ticket_url)

		session_id = data.cookies['JSESSIONID']
		unk1 = data.cookies['NSC_wtsw_sfntnbsujuwq_8443_ofx']

		self.remedy.session_properties = {
			"JSESSIONID" : session_id,
			"NSC_wtsw_sfntnbsujuwq_8443_ofx" : unk1
		}

	def get_asset_name(self, ticket_id):
		# Returns the computer name if one
		data = self.session.get(self.remedy.get_desc(ticket_id), cookies=self.remedy.session_properties)
		data = data.json()
		data = data[0]['items'][0]
		data = data['desc']

		if 'Asset ID:' in data:
			asset_id = data.index('Asset ID:')
			index = len('Asset ID:') + asset_id
			computer_name = data[index : index + 15].strip()
			return computer_name

		return False

	def new_ticket(self, ticket_id, ticket_summary):
		computer_name = self.get_asset_name(ticket_id)
		msg = "New ticket..."
		if computer_name:
			asset = self.remedy.get_asset(computer_name)
			cart_msg = "For a cart" if asset.is_cart else "For a PC"

			msg += f"{cart_msg} located at {asset.tower} {asset.floor}..."

		if not "Easy" in ticket_summary:
			msg += ticket_summary
			
		self.alert()
		if(len(msg) > 13):
			self.speak(msg)
		
	def get_tickets(self):
		data = self.session.post(self.remedy.ticket_url, cookies=self.remedy.session_properties, 
				json=self.remedy.payload)

		if data.status_code == 200:
			tickets = data.json()
			tickets = tickets[0]['items'][0]['objects']

			# This adds tickets to the list
			skip = False
			output_msg = ""
			for ticket in tickets:
				ticket_id = ticket['id']
				ticket_summary = ticket['summary']
				ticket_type = ticket['type']

				if not ticket_id in self.tickets:
					# We always want to skip the first batch
					if len(self.tickets) == 0:
						skip = True

					if not skip:
						self.new_ticket(ticket_id, ticket_summary)
					self.tickets.append(ticket_id)

				output_msg += f"{ticket_id} {ticket_type} {ticket_summary}\n"

			os.system('cls')
			print(output_msg)
			time.sleep(10)

	def start(self):
		self.get_session()
		self.remedy.login(self.session)
		while True:
			try:
				self.get_tickets()

			except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
				self.connect_server()

			except Exception as e:
				self.speak("Unknown error, look at the logs for details.")
				print(e)
				exit()

	def speak(self, msg):
		self.voice_engine.say(msg)
		self.voice_engine.runAndWait()

	def alert(self):
		winsound.PlaySound('alert.wav', winsound.SND_FILENAME)

	def connect_server(self):
		# This will handle disconnects and re-connects
		for _ in range(20):
			try:
				self.get_tickets()
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
