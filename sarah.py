#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import pyttsx3
import requests
import time


class API:
	def __init__(self):
		self.engine = pyttsx3.init()

		# Set the voice properties
		self.engine.setProperty('voice', 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0')
		self.engine.setProperty('rate', 155)
		self.engine.setProperty('volume', 1)
		self.connect_limit = 5

		with requests.session() as s:
			#self.speak('Good morning, connecting to server.')
			while True:
				self.connect_server(s)
			else:
				self.speak("I was unable to connect to the server.")


	def speak(self, msg):
		self.engine.say(msg)
		self.engine.runAndWait()

	def get_location(self, asset_name):
		asset_name = asset_name.strip()
		if len(asset_name) != 15:
			return None

		towers = {
			'WT' : 'West Tower',
			'ET' : 'East Tower'
		}

		tower = towers[asset_name[1 : 3]]
		floor = str(int(asset_name[4 : 6]))
		is_cart = 'CWM' in asset_name

		msg = f"{tower} {floor}"
		msg += "...This is a cart" if is_cart else "...This is a PC"

		return msg

	def connect_server(self, s):
		if self.connect_limit <= 0:
			self.speak("I could not re-connect to the server, ending session.")
			exit()
		try:
			response = s.get('http://orteil.dashnet.org/cookieclicker/', timeout=1)

			self.speak("New ticket")
			self.speak("Monitor is black")

			#Simulate a ticket
			asset_name = 'BWTB0300511CWMP'
			location = self.get_location(asset_name)
			if location:
				self.speak(location)

			self.connect_limit = 5
			exit()

		# If the connection failed
		except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
			if self.connect_limit == 5:
				self.speak("I was disconnected from the server, trying to re-connect.")

			print(f"Error: Disconnected, connection attempts left: {self.connect_limit}")
			self.connect_limit -= 1
			time.sleep(3)

if __name__ == '__main__':
	API()
