from django.shortcuts import render
from django.http.response import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
import requests
import time
import random

apiKey = "AIzaSyDwtlwHszBEkwvJ3ELfl0YW_EAVV0_44LI"

class CommandView(APIView):
	def get(self, request):
		return Response({"eat": request.query_params})

	def post(self, request):
		global apiKey
		cmd, option = request.data.get("item").get("message").get("message").split()
		msgID = request.data.get("item").get("message").get("id")

		if cmd == "/food":
			if option == "random":
				places = self.getNearByFood(apiKey)
				food = self.getRandomPlace(places)
				foodDetails = self.getPlaceDetails(food["place_id"], apiKey)
				return Response(self.generateHipChatFoodMSG(foodDetails, msgID))
			elif option == "help":
				return Response(self.generateHelpMSG())
			else: 
				return Response(self.generateGenericHipChatMSG('"{}" Dunno that one...'.format(option)))
		else:
			return Response("Error, unknown command", status=404)

	def generatePlaceURL(self, key, pageToken=None, placeID=None):
		url = ""
		if placeID:
			url = "https://maps.googleapis.com/maps/api/place/details/json?"
		else:
			url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?"

		if placeID:
			url += "placeid=" + placeID
		elif pageToken:
			url += "pagetoken=" + pageToken
		else:
			url += "location=42.423916,-83.427546" #livonia office lol
			url += "&radius=7000" #within 6ish miles
			url += "&type=restaurant" #food plz 

		url += "&key=" + key

		return url

	def generateGenericHipChatMSG(self, msg):
		toSend = {
			"color": "yellow",
			"notify": False,
			"message_format": "text",
			"message": msg
		} 

		return toSend

	def generateHelpMSG(self):
		toSend = {
			"color": "yellow",
			"notify": False,
			"message_format": "text",
			"message": "/food [random/help]\nMore commands coming soon."
		} 

		return toSend

	def generateHipChatFoodMSG(self, details, msgID):
		toSend = {
			"color": "green",
			"notify": False,
			"message_format": "text"
		}
		
		toSend["message"] = details["name"] + "\n" + details["website"]
		toSend["card"] = self.generateHipChatURLCard(details, msgID)

		return toSend

	def generateHipChatURLCard(self, details, msgID):
		card = {
			"style": "application",
			"url": details["website"],
			"format": "medium",
			"id": msgID,
			"title": details["name"],
			"description": "Review: " + details["reviews"][0]["text"],
			"icon": {
				"url": details["icon"]
			},
			"attributes": self.generateCardAttributes(details)
		}

		return card

	def generateCardAttributes(self, details):
		attrs = ["price_level", "rating"]
		attributes = []

		for attr in attrs:
			attribute = {
				"label": attr.split('_')[0].title(),
				"value": {
					"label": str(details[attr]).title(),
					"style": self.getAttrStyle(details[attr], True if attr == "price_level" else False) #yikes...
				}
			}
			attributes.append(attribute)
		return attributes

	def getNearByFood(self, key):
		results = []
		nearbyURL = self.generatePlaceURL(key)
		r = requests.get(nearbyURL)
		response = r.json()
		results += response["results"]

		if "next_page_token" in response:
			nextPageResponse = self.getNextPage(response["next_page_token"], key)
			results += nextPageResponse["results"]

		return results
		
	'''
	There is a short delay between when a next_page_token is issued, and when it will become valid. 
	Requesting the next page before it is available will return an INVALID_REQUEST response. 
	Retrying the request with the same next_page_token will return the next page of results.
	'''
	def getNextPage(self, token, key):
		attemps = 1
		time.sleep(2)
		nextNearbyURL = self.generatePlaceURL(key, token)
		r = requests.get(nextNearbyURL)
		response = r.json()
		while (response["status"] == "IINVALID_REQUEST"):
			print("attempt", attemps)
			time.sleep(0.3)
			r = requests.get(nextNearbyURL)
			attemps += 1
			if attemps > 3:
				break
		return r.json()

	def getRandomPlace(self, places):
		randIndex = random.randint(0, len(places) - 1);
		randPlace = places[randIndex]
		return randPlace

	def getPlaceDetails(self, placeID, key):
		placeDetailURL = self.generatePlaceURL(key, None, placeID)
		r = requests.get(placeDetailURL)
		return r.json()["result"]

	def getAttrStyle(self, val, price):
		if val <= 1:
			return "lozenge-success" if price else "lozenge-error"
		elif val <= 3.3 and val >= 2:
			return "lozenge-current" if price else "lozenge"
		elif val > 3.3 and val <= 4:
			return "lozenge-error" if price else "lozenge-complete"
		elif val > 4:
			return "lozenge-error" if price else "lozenge-success"