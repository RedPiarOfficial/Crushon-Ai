from typing import List, Dict, Any
import cloudscraper
import json



class Client:
	BASE_URL = "https://crushon.ai"
	API_URL = f"{BASE_URL}/api"

	def __init__(self):
		self.scraper = cloudscraper.create_scraper()
		self.cookies = {}

	def login(self, email: str) -> int:
		csrf_token = self._fetch_csrf_token()
		response = self.scraper.post(
			f"{self.API_URL}/auth/signin/email",
			json={
				"email": email,
				"callbackUrl": f"{self.BASE_URL}/account/",
				"csrfToken": csrf_token,
				"json": True
			}
		)
		response.raise_for_status()
		return response.status_code

	def _fetch_csrf_token(self) -> str:
		response = self.scraper.get(f"{self.API_URL}/auth/csrf")
		response.raise_for_status()
		return response.json().get("csrfToken")

	def session(self):
		csrf_token = self._fetch_csrf_token()
		response = self.scraper.post(
			f"{self.API_URL}/auth/session",
			json={"csrfToken": csrf_token}
		)
		response.raise_for_status()
		return response.json()

	def set_cookies(self, cookies: Dict[str, str]) -> Dict[str, Any]:
		for name, value in cookies.items():
			self.scraper.cookies.set(name, value)
		data = self.session()
		self.cookies = self.scraper.cookies.get_dict()
		return data

	def confirm(self, auth_url: str) -> Dict[str, Any]:
		response = self.scraper.get(auth_url, allow_redirects=True)
		response.raise_for_status()
		data = self.session()
		self.cookies = self.scraper.cookies.get_dict()
		return data

	def get_recommendations(self, count: int = 25, nsfw: bool = False, gender: int = 0, tags: List[str] = []) -> Dict[str, Any]:
		params = {
			'batch': 1,
			'input': json.dumps({
				"0": {
					"json": {
						"tags": tags,
						"collectionKind": "",
						"sortTag": "recent-hits",
						"nsfw": nsfw,
						"gender": gender,
						"count": count,
						"locale": "en",
						"flyingNsfw": False,
						"direction": "forward"
					}
				}
			})
		}
		response = self.scraper.get(
			f"{self.API_URL}/trpc/character.getCharactersByTag",
			params=params,
			headers={"x-nsfw": 'true' if nsfw else 'false', "x-gender": str(gender)}
		)
		response.raise_for_status()
		return response.json()[0]["result"]["data"]["json"]

	def search(self, query: str, nsfw: bool = False, count: int = 20, cursor: int = 0, tags: List[str] = []) -> Dict[str, Any]:
		response = self.scraper.post(
			f"{self.API_URL}/trpc/character.searchInfinite?batch=1",
			json={"0": {"json": {
				"query": query,
				"limit": count,
				"nsfw": nsfw,
				"gender": 0,
				"tags": tags,
				"sortTag": "all",
				"cursor": cursor,
				"pager": {"count": count, "total": -1, "offset": 0, "external": ""},
				"locale": "ru"
			}}},
			headers = {"x-nsfw": 'true' if nsfw else 'false'}
		)
		response.raise_for_status()
		return response.json()[0]["result"]["data"]["json"]

	def get_tags(self) -> Dict[str, Any]:
		params = {
			'batch': 1,
			'input': json.dumps({"0": {"json": {"locale": "ru", "nsfw": False}}})
		}
		response = self.scraper.get(
			f"{self.API_URL}/trpc/character.getSearchFilterTags",
			params=params,
			headers={"content-type": "application/json"}
		)
		response.raise_for_status()
		return response.json()[0]["result"]["data"]["json"]

	def invite_code(self) -> Dict[str, Any]:
		params = {
			'batch': 1,
			'input': json.dumps({
				"0": {"json": {"isOwn": True}},
				"1": {"json": None, "meta": {"values": ["undefined"]}}
			})
		}
		response = self.scraper.get(
			f"{self.API_URL}/trpc/character.queryUserCharacters,user.queryInvitation",
			params=params
		)
		response.raise_for_status()
		return response.json()[1]["result"]["data"]["json"]

	def active_code(self, code: str) -> Dict[str, Any]:
		response = self.scraper.post(
			f"{self.API_URL}/trpc/user.submitInvitationCode?batch=1",
			json={"0": {"json": {"code": code}}}
		)
		response.raise_for_status()
		return response.json()

	def complete_task(self, type: int) -> Dict[str, Any]:
		response = self.scraper.post(
			f"{self.API_URL}/trpc/task.submitTask?batch=1",
			json={"0": {"json": {"taskType": int(type)}}}
		)
		response.raise_for_status()
		return response.json()

	def tasks(self) -> None:
		'''
		Retrieves tasks with the following statuses:
		1 - Available for completion
		2 - Completed
		3 - Expired or unavailable
		'''
		params = {
			'batch': 1,
			'input': json.dumps({
				"0": {"json": None, "meta": {"values": ["undefined"]}},
				"1": {"json": None, "meta": {"values": ["undefined"]}},
				"2": {"json": {}},
				"3": {"json": {"survey_entry": "task"}},
				"4": {"json": {"isOwn": True}},
				"5": {"json": None, "meta": {"values": ["undefined"]}}
			})
		}
		response = self.scraper.get(
			f"{self.API_URL}/trpc/task.getTaskRedDot,achievement.getRedDot,account.queryAccountInfo,task.getTasks,character.queryUserCharacters,user.queryInvitation",
			params=params
		)
		response.raise_for_status()
		tasks = response.json()[3]["result"]["data"]["json"]["tasks"]
		return tasks

	def inbox(self) -> Dict[str, Any]:
		params = {
			'batch': 1,
			'input': json.dumps({
				"0": {"json": {"nsfw": True, "locale": "ru"}},
				"1": {"json": None, "meta": {"values": ["undefined"]}},
				"2": {"json": None, "meta": {"values": ["undefined"]}},
				"3": {"json": None, "meta": {"values": ["undefined"]}},
				"4": {"json": None, "meta": {"values": ["undefined"]}},
				"5": {"json": None, "meta": {"values": ["undefined"]}},
				"6": {"json": {"blockTargetTypes": [3, 2, 1]}}
			})
		}
		response = self.scraper.get(
			f"{self.API_URL}/trpc/character.queryRecentCharacters,group.getGroupList,account.queryUserProfile,task.getTaskRedDot,achievement.getRedDot,notifications.getUnreadCount,account.getBlockList",
			params=params
		)
		response.raise_for_status()
		return response.json()[0]["result"]["data"]["json"]