import requests

def update_player(player=None):
    pass

def get_stats(character_id=None):
	url = 'https://www.dndbeyond.com/character/{}/json'.format(character_id)
	data = requests.get(url)
	if data.status_code == requests.codes.ok:
		return data.json()
