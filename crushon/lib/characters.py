import uuid
from datetime import datetime
from dateutil.parser import parse
from typing import List, Dict, Any
import json
def find_newest_objects(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
	"""
	Finds objects with the most recent 'created_at' values.

	Args:
		data: A list of dictionaries, each representing an object with a 'created_at' field.

	Returns:
		A list of dictionaries representing the objects with the most recent 'created_at' values.
	"""

	def extract_datetime(obj: Dict[str, Any]) -> datetime:
		"""
		Extracts and parses the 'created_at' date from a dictionary object.

		Args:
			obj: A dictionary containing a 'created_at' field.

		Returns:
			A datetime object parsed from the 'created_at' field.

		Raises:
			ValueError: If the object does not contain 'created_at' or is not a dictionary.
		"""
		if isinstance(obj, dict) and 'created_at' in obj:
			return parse(obj['created_at'])
		raise ValueError("Object must be a dictionary with 'created_at' field")

	# Filter and sort the data by 'created_at' in descending order
	filtered_data = [obj for obj in data if obj.get('content')]
	filtered_data.sort(key=extract_datetime, reverse=True)

	return filtered_data

class Characters:
	def __init__(self, client):
		"""
		Initializes the Characters instance with a Client object.

		Args:
			client: An instance of the Client class.
		"""
		self.client = client
		self.scraper = client.scraper

	def get_character(self, charid) -> List[Dict[str, Any]]:
		"""
		Retrieves character data from the API.

		Returns:
			A list of dictionaries representing character data.
		"""
		params = {
			'batch': 1,
			'input': json.dumps({
						"0":{"json":{"characterId":charid}},
						"1":{"json":None,"meta":{"values":["undefined"]}}
						})
		}
		response = self.scraper.get(
			"https://crushon.ai/api/trpc/chat.getLatestConversation,account.getUsageDetail",
			params=params
		)
		response.raise_for_status()

		return response.json()[0]["result"]["data"]["json"]

	def get_history(self, charid):
		histories = self.get_character(charid)
		data = []
		for history in histories["mapping"]:
			data.append({
							"id":history[1]["id"],
							"created_at": history[1]["created_at"],
							"content": history[1]["content"],
							"role": history[1]["role"],
						})
		newest_objects = find_newest_objects(data)
		return newest_objects

	def send_message(self, text: str, charid: str) -> None:
		"""
		Sends a message using the API, referencing the most recent conversation.

		Args:
			text: The content of the message to be sent.
		"""
		newest_objects = self.get_history(charid)
		charData = self.get_character(charid)

		payload = {
			"0": {
				"json": {
					"type": 1,
					"parentMessageId": newest_objects[0]["id"],
					"contextMessageIds": [obj["id"] for obj in newest_objects],
					"content": text,
					"conversationId": charData["conversation"]["id"],
					"inferenceOption": {
						"model": "co-llm-taurus",
						"maxTokens": 175,
						"temperature": 0.7,
						"topP": 0.7
					},
					"extendedInferenceOption": {
						"enhancedImmersion": False,
						"preferLanguage": "english",
						"style": "default"
					}
				}
			}
		}

		response = self.scraper.post(
			"https://crushon.ai/api/trpc/chat.chatV3?batch=1",
			json=payload
		)
		response.raise_for_status()
		return response.json()[0]["result"]["data"]["json"]
