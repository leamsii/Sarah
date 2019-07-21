#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import pyttsx3
import requests
import time


class Asset:
	def __init__(self, tower, floor, is_cart):
		self.tower = tower
		self.floor = floor
		self.is_cart = is_cart


class Remedy:
	def __init__(self):
		self.towers = {
			'WT' : 'West Tower',
			'ET' : 'East Tower'
		}
		# Get the session id cookie here
		self.base_url = 'http://orteil.dashnet.org/cookieclicker/'


	def get_asset_info(self, asset_name):
		asset_name = asset_name.strip() # Remove any spaces
		if len(asset_name) != 15:
			return None

		tower = self.towers[asset_name[1 : 3]]
		floor = str(int(asset_name[4 : 6]))
		is_cart = 'CWM' in asset_name

		return Asset(tower, floor, is_cart)

class API:
	def __init__(self):
		self.engine = pyttsx3.init()

		# Set the voice properties
		self.engine.setProperty('voice', 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0')
		self.engine.setProperty('rate', 155)
		self.engine.setProperty('volume', 1)
		
		# Keep track of tickets
		self.tickets = []

		# Create a Remedy object
		self.remedy = Remedy()

		with requests.session() as s:
			self.speak("Searching tickets")
			while True:
				try:
					print("Main program")
					response = s.get(self.remedy.base_url) # Simulate getting ticket data
					self.update_ticket_list(response.text)
					time.sleep(1)

				except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
					self.speak("Sir, I was disconnected from the server, trying to re-connect")
					self.connect_server(s)

				except Exception as e:
					self.speak("Unknown error, look at the logs for details.")
					print(e)
					exit()

	def update_ticket_list(self, resp):

		"""
		In this function we will check if we have any new tickets
		First by comparing the length of our current ticket array
		Then checking if the IDS don't match
		After, we get the summary and ticket location
		If our array for the day is empty, skip the first batch
		"""

		# Simulate new ticket
		summary = "The computer won't turn on."
		asset = self.remedy.get_asset_info(f'BWTB0900511CWMP')

		if asset:
			cart_msg = "...This is a cart" if asset.is_cart else "...This is a PC"
			self.speak(f"New ticket...Located at {asset.tower} {asset.floor}{cart_msg}...User says {summary}")
		else:
			self.speak(f"New ticket...User says {summary}")

	def speak(self, msg):
		self.engine.say(msg)
		self.engine.runAndWait()

	def connect_server(self, s):
		# This will handle disconnects and re-connects
		for _ in range(10):
			try:
				response = s.get(self.remedy.base_url, timeout=1)
				self.speak("Re-connected to server")
				break

			except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
				print(f"Error: Disconnected, connection attempts left: {_}")
				time.sleep(3)
		else:
			self.speak("Could not establish a connection, ending session")
			exit()


if __name__ == '__main__':
	API()