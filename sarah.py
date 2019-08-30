
# Dependencies
import requests
import pyttsx3
#-------------
import time
import os
import winsound
import sys
import getpass
import re
from colorama import Fore, Back, Style 


# Make sure Python 3+ is running
if not sys.version_info >= (3, 0):
	print("Error: Please upgrade to Python 3+")
	exit()

# Define global variables
TOWERS = {
'ET' : 'East Tower',
'WT' : 'West Tower',
'NE' : 'North East',
'NW' : 'North West',
'PO' : 'Podium',
'PT' : 'The E-D',
'RY' : 'Perry',
'MH' : 'Mill Hill',
'MS' : 'Mill Hill'
}

REFRESH_RATE = 10 # How often tickets are refreshed
CONNECTION_ATTEMPTS = 100 # How many times is Sarah allowed to attempt to reconnect after d/c

class Asset:
	def __init__(self, asset_name):

		# This will collect the asset location
		self.tower = TOWERS[asset_name[1 : 3]]
		self.cart = 'CWM' in asset_name

		# Must wrap this when converting string to int
		try:
			self.floor = str(int(asset_name[4 : 6]))
		except ValueError:
			self.floor = ''

class Ticket:
	def __init__(self, data):
		self._id = data['id']
		self.summary = data['summary']
		self.type = data['type']

# Remedy API
class Remedy:
	def __init__(self):

		self.urls = {
			"get_ticket": "https://remsmartitvp.ynhh.org:8443/ux/rest/v2/person/workitems/get",
			"get_desc"  : "https://remsmartitvp.ynhh.org:8443/ux/rest/v2/incident/",
			"login_url" :"https://remsmartitvp.ynhh.org:8443/ux/rest/users/sessions/"
		}

		# Set payload
		self.payload = {"filterCriteria":{"assignedSupportGroups":[{"name":"Desktop Support - BH","company":{"name":"Yale New Haven Health"},
		"organization":"IT Support","isDefault":True,"id":"SGP000000000184"}],"statusMappings":["open"],
		"ticketTypes":["incident"]},"chunkInfo":{"startIndex":0,"chunkSize":75},"sortInfo":{},
		"attributeNames":["priority","id","assignee","summary","status","submitDate"],"customAttributeNames":[]}


	def login(self, session):
		username = input("Username: ").strip().lower()
		password = getpass.getpass().strip()

		payload = {"password": password,"appName":"Galileo","appVersion":"2.0.00.000","apiVersion":1600000,"locale":"en","deviceToken":"dummyToken",
			"os":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36","model":"Web Client"}

		# Send payload information to server
		response = session.post(self.urls['login_url'] + username, cookies = self.session_properties, json = payload)

		# If login success
		if response.status_code == 200:
			os.system("cls")
		else:
			print("Error: Invalid credentials")
			self.login(session)

	def set_session(self):
		# This function will return a new session
		session = requests.session()
		data = session.get(self.urls['get_ticket']) # Request some data

		# Set the cookies for the session
		self.session_properties = {
			"JSESSIONID" : data.cookies['JSESSIONID'],
			"NSC_wtsw_sfntnbsujuwq_8443_ofx" : data.cookies['NSC_wtsw_sfntnbsujuwq_8443_ofx']
		}
		return session


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

		self.start()

	def start(self):
		self.session = self.remedy.set_session() # Get the new session from the Remedy API
		self.remedy.login(self.session) # Have the user login

		self.speak("Searching tickets...")

		# Main loop
		while True:
			try:
				self.get_tickets()

			except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
				self.connect_server()

			except Exception as e:
				self.speak("Unknown error, look at the logs for details.")
				print(e)
				exit()


	def get_tickets(self):
		# Send a request to the server with correct header
		response = self.session.post(self.remedy.urls['get_ticket'], cookies = self.remedy.session_properties, 
				json = self.remedy.payload)

		# Success
		result_msg = ""
		if response.status_code == 200:
				ticket_list = response.json()[0]['items'][0]['objects']

				if len(self.tickets) == 0:
					for _ in ticket_list:
						self.tickets.append(Ticket(_)._id) # Skip the first batch
					return
				else:
					# Handle new tickets
					for k,data in enumerate(ticket_list):
						new_ticket = Ticket(data)
						if not new_ticket._id in self.tickets:
							self.update_tickets(new_ticket)
							self.tickets.append(new_ticket._id)

						result_msg += f"[{k}]\t{new_ticket.summary}"

						# Show asset location
						asset_name = self.get_asset_name(new_ticket)
						if asset_name:
							asset = Asset(asset_name.upper())
							result_msg += Fore.YELLOW + f" ({asset.tower} {asset.floor})" + Style.RESET_ALL
						result_msg += "\n"

				# Show the list of tickets
				os.system('cls')
				print(Back.GREEN + "Sarah  Version 2.0\n" + Style.RESET_ALL)
				print(result_msg)
				time.sleep(REFRESH_RATE)

	def get_asset_name(self, ticket):
		# Returns the computer name if one
		response = self.session.get(self.remedy.urls['get_desc'] + ticket._id, cookies = self.remedy.session_properties)
		data = response.json()
		data = data[0]['items'][0]
		data = data['desc']

		# Use regular expressions to loop through the description for a asset location
		computer_name = re.search('\D\D\D\D\d\d\d\d\d\d\d\D\D\D\D', data)
		try:
			return computer_name.group()
		except:
			try:
				computer_name = re.search('\D\D\D\D\d\d\d\d\d\d\d\D\D\D\D', ticket.summary)
				return computer_name.group()
			except:
				return False

	def update_tickets(self, ticket):
		computer_name = self.get_asset_name(ticket) # Get the computer name
		msg = "New ticket..."
		if computer_name:
			asset = Asset(computer_name.upper())

			cart_msg = "For a cart" if asset.cart else "For a PC"
			msg += f"{cart_msg} in {asset.tower} {asset.floor}..."

		# Skip easy button pressed
		if not "Easy" in ticket.summary:
			msg += ticket.summary

		# If not created by IT agent
		if not ticket.summary.startswith('BH'):
			self.alert()
			self.speak(msg)

	def speak(self, msg):
		self.voice_engine.say(msg)
		self.voice_engine.runAndWait()

	def alert(self):
		winsound.PlaySound('alert.wav', winsound.SND_FILENAME)

	def connect_server(self):
		# This will handle disconnects and re-connects
		for _ in range(CONNECTION_ATTEMPTS):
			try:
				self.get_tickets()
				break

			except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
				print(f"Error: Disconnected, connection attempts made: {_}")
				time.sleep(5)
		else:
			self.speak("Could not establish a connection, ending session")
			exit()

if __name__ == '__main__':
	print("Log: Connecting to server..")
	Sarah()

