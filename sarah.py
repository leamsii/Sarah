#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import pyttsx3
import requests
import time


class Remedy:
	def __init__(self):
		self.towers = {
			'WT' : 'West Tower',
			'ET' : 'East Tower'
		}

	def get_asset_info(self, asset_name):
		asset_name = asset_name.strip() # Remove any spaces
		if len(asset_name) != 15:
			return None

		tower = self.towers[asset_name[1 : 3]]
		floor = str(int(asset_name[4 : 6]))
		is_cart = 'CWM' in asset_name

		msg = f"Located at {tower} {floor}"
		msg += "...This is a cart" if is_cart else "...This is a PC"
		return msg

class API:
	def __init__(self):
		self.engine = pyttsx3.init()

		# Set the voice properties
		self.engine.setProperty('voice', 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0')
		self.engine.setProperty('rate', 155)
		self.engine.setProperty('volume', 1)
		self.base_url = 'http://orteil.dashnet.org/cookieclicker/'

		# Create a Remedy object
		self.remedy = Remedy()

		with requests.session() as s:
			self.speak("Searching tickets..")
			while True:
				try:
					print("Main program")

					# Simulate new ticket
					ticket_location = self.remedy.get_asset_info(f'BWTB0900511CWM')
					if ticket_location:
						self.speak("New Ticket..." + ticket_location)

					# The summary
					self.speak("New ticket...User complaint the mouse is not working.")

					# Test data
					response = s.get(self.base_url)
					time.sleep(1)

				except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
					self.speak("Sir, I was disconnected from the server, trying to re-connect")
					self.connect_server(s)

				except Exception as e:
					self.speak("Unknown error, look at the logs.")
					print(e)
					exit()

	def speak(self, msg):
		self.engine.say(msg)
		self.engine.runAndWait()

	def connect_server(self, s):
		# This will handle disconnects and re-connects
		for _ in range(10):
			try:
				response = s.get(self.base_url, timeout=1)
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