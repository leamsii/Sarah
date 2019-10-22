
# -*- coding: utf-8 -*-
# Dependencies make sure to install these using pip

#The URL links to the server were removed for security reasons, this project is now for educational purposes only.


import requests
import pyttsx3
from colorama import Fore, Back, Style
#-------------
import time
import os
import winsound
import sys
import getpass
import re


# Make sure Python 3+ is running
if not sys.version_info >= (3, 0):
	print("Error: Please upgrade to Python 3+")
	exit()

# These are the tower location dependent of the hospital
TOWERS = {
'ET' : 'East Tower',
'WT' : 'West Tower',
'NE' : 'North East',
'NW' : 'North West',
'PO' : 'Podium',
'PT' : 'The E-D',
'ED' : 'The E-D',
'PR' : 'Perry',
'BR' : 'Perry',
'MH' : 'Mill Hill',
'MS' : 'Marsh',
'2M' : 'Albin',
'WH' : 'White House'
}

REFRESH_RATE = 10 # How often tickets are refreshed
CONNECTION_ATTEMPTS = 100 # How many times is Sarah allowed to attempt to reconnect after d/c

class Asset:
	def __init__(self, asset_name):

		# This will collect the asset location
		self.name = asset_name
		self.tower = TOWERS[asset_name[1 : 3]] if TOWERS.get(asset_name[1 : 3]) else "Unknown"
		self.cart = 'CWM' in asset_name
		self.floor = int(asset_name[4 : 6]) if asset_name[4 : 6].isdigit() else ""
		
		if self.floor and self.floor > 10:
			self.floor = ""


class Ticket:
	def __init__(self, data):
		self._id = data['id']
		self.summary = data['summary']
		self.type = data['type']
		self.asset = None

# Remedy API
class Remedy:
	def __init__(self):

		self.urls = {
			"get_ticket": "",
			"get_desc"  : "",
			"login_url" :""
		}

		# Set payload
		self.payload = {}


	def login(self, session):
		username = input("Username: ").strip()
		password = getpass.getpass().strip()

		payload = {}

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
		self.tickets = {}
		self.start()

	def start(self):
		print("Log: Connecting to server.")

		self.session = self.remedy.set_session() # Get the new session from the Remedy API
		self.remedy.login(self.session) # Have the user login
		self.speak("Searching tickets...")

		# Main loop
		while True:
			try:
				self.get_tickets()
			except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
				# If lost connection, reconnect
				self.connect_server()

			except Exception as e:
				self.speak("Unknown error, look at the logs for details.")
				print(e)
				os.system("PAUSE")
				exit()


	def get_tickets(self):
		# Send a request to the server with correct header
		response = self.session.post(self.remedy.urls['get_ticket'], cookies = self.remedy.session_properties, 
				json = self.remedy.payload)

		# Handles new and old tickets
		if response.status_code == 200:
				# Grab the list of tickets currently in the queue
				ticket_list = response.json()[0]['items'][0]['objects']

				# Skip the first batch
				if not self.tickets:
					for data in ticket_list:
						# Assign an asset to the ticket and add it to the list
						self.add_ticket(Ticket(data))
					return

				# Search for new tickets
				result_msg = ""
				for key, data in enumerate(ticket_list):
					current_ticket = Ticket(data)
					if not self.tickets.get(current_ticket._id): # New ticket
						self.add_ticket(current_ticket, True)

					# Update the summary
					self.tickets.get(current_ticket._id).summary = current_ticket.summary
					
					current_ticket = self.tickets.get(current_ticket._id)
					result_msg += f"[{key}]\t{current_ticket.summary}"
					if current_ticket.asset:
						result_msg += Fore.YELLOW + f" ({current_ticket.asset.tower} {current_ticket.asset.floor})" + Style.RESET_ALL
					result_msg += "\n"
					
				# Show the list of tickets
				os.system('cls')
				print(Back.GREEN + "Sarah  Version 2.0\n" + Style.RESET_ALL)
				print(result_msg)
				time.sleep(REFRESH_RATE)

	def add_ticket(self, ticket, announce=False):
		self.tickets[ticket._id] = ticket
		# Give it an asset
		asset_name = self.get_asset_name(ticket)
		if asset_name:
			ticket.asset = Asset(asset_name.upper())

		# Announce it
		if announce:
			msg = "New ticket..."
			if ticket.asset:
				cart_msg = "For a cart" if ticket.asset.cart else "For a PC"
				msg += f"{cart_msg} in {ticket.asset.tower} {ticket.asset.floor}..."

			# If not created by IT agent
			if not ticket.summary.startswith('BH'):
				# Skip easy button pressed
				if not "Easy" in ticket.summary:
					msg += ticket.summary

				# Handle O-R Alerts
				if "BPT-OR-Alert" in ticket.summary:
					msg += "OR-Alert"

				# Speak
				self.alert()
				self.speak(msg)

	def get_asset_name(self, ticket):
		# Returns the computer name if found
		response = self.session.get(self.remedy.urls['get_desc'] + ticket._id, cookies = self.remedy.session_properties)
		data = response.json()
		data = data[0]['items'][0]
		data = data['desc']

		# Use regular expressions to loop through the description and summary for the computer name
		computer_name = re.search('\D\S\D\D\d\d\d\d\S\S\S\D\D\D\D', data + ticket.summary)
		return False if not computer_name else computer_name.group()


	def speak(self, msg):
		self.voice_engine.say(msg)
		self.voice_engine.runAndWait()

	def alert(self):
		winsound.PlaySound('alert.wav', winsound.SND_FILENAME)

	def connect_server(self):
		# This will handle disconnects and re-connects
		print("Log: Lost connection to server, re-connecting..")
		for _ in range(CONNECTION_ATTEMPTS):
			try:
				self.get_tickets()
				break

			except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
				time.sleep(5)
		else:
			self.speak("Could not establish a connection, ending session")
			exit()

if __name__ == '__main__':
	Sarah()

