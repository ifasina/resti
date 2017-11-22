from django.shortcuts import render
from django.http.response import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
import requests
import time
import random

class CommandView(APIView):
	def get(self, request):
		return Response({"eat": request.query_params})

	def post(self, request):
		cmd = request.data.get("item").get("message").get("message")
		places = self.getNearByFood()


		
		if cmd == "/random":
			food = self.getRandomPlace(places)
			return Response(self.generateHipChatMSG(food["name"]))

	def generateHipChatMSG(self, msg):
		toSend = {
			"color": "blue",
			"message": msg,
			"notify": False,
			"message_format": "text"
		}

		return toSend

	def getNearByFood(self):
		results = []
		nearbyURL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=42.423916,-83.427546&radius=7000&type=restaurant&key=AIzaSyDwtlwHszBEkwvJ3ELfl0YW_EAVV0_44LI"
		r = requests.get(nearbyURL)
		response = r.json()
		results += response["results"]

		print("before", len(results))

		if "next_page_token" in response:
			nextPageResponse = self.getNextPage(response["next_page_token"])
			results += nextPageResponse["results"]

		return results
		
	'''
	There is a short delay between when a next_page_token is issued, and when it will become valid. 
	Requesting the next page before it is available will return an INVALID_REQUEST response. 
	Retrying the request with the same next_page_token will return the next page of results.
	'''
	def getNextPage(self, token):
		attemps = 1
		time.sleep(2)
		nextNearbyURL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?pagetoken=" + token + "&key=AIzaSyDwtlwHszBEkwvJ3ELfl0YW_EAVV0_44LI"
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
