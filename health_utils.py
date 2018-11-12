import requests

class ThrottlingException(Exception):
	pass 

def get_health_status_color(current_hp):
	if current_hp == 0:
		status = 'secondary'
	elif 0 > current_hp < 34:
		status = 'danger'
	elif current_hp > 66:
		status = 'success'
	else:
		status = 'warning'
	return status

def more_con(modifier_data):
    extra_con = 0
    for mod in modifier_data:
        if mod['entityId'] == 3 and mod['entityTypeId'] == 1472902489 and mod['value'] != None:
            extra_con += mod['value']
    return extra_con


def tough_hp(character_level, feats):
    feat_hp = 0
    for feat in feats:
        if feat['componentId'] == 49 and feat['componentTypeId'] == 1088085227 and feat['value'] != None:
            feat_hp = character_level * feat['value']
    return feat_hp


def get_character_health(character_id):
    url = 'https://www.dndbeyond.com/character/{}/json'.format(character_id)
    response = requests.get(url)
    if response.status_code == 429:
    	print('ThrottlingException - ',  response.status_code)
    	print(response.content)
    	raise ThrottlingException

    data = response.json()

    if data['bonusStats'][2]['value'] != None:
        manual_con = data['bonusStats'][2]['value']
    else:
        manual_con = 0

    if 'bonusHitPoints' in data.keys() and data['bonusHitPoints'] is not None:
    	bonus_hp = data['bonusHitPoints']
    else:
    	bonus_hp = 0

    base_hp = data['baseHitPoints']
    base_con = data['stats'][2]['value']
    con_stat = base_con + manual_con

    for modifier in ('race', 'class', 'items'):
    	try:
    		con_stat += more_con(data['modifiers'][modifier])
    	except KeyError:
    		pass

    con_mod = (con_stat - 10) // 2
    character_level = 0

    for dnd_class in data['classes']:
        character_level += int(dnd_class['level'])

    con_hp = con_mod * character_level
    max_hp = base_hp + con_hp + tough_hp(character_level, data['modifiers']['feat']) + bonus_hp
    current_hp = round(((max_hp - data['removedHitPoints']) / max_hp) * 100 )
    return {'base_hp': base_hp, 'con_stat': con_stat, 'current_hp': current_hp, 'name': data['name'], 'health_status': get_health_status_color(current_hp)}

