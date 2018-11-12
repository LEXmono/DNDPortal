from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, UTCDateTimeAttribute)
from datetime import datetime


class Character(Model):
    def __init__(self, character_id=None, name=None, initiative=0, init_mod=0, health=None, health_status=None):
        self.character_id = character_id
        self.name = name
        self.initiative = initiative
        self.initiative_mod = init_mod
        self.health = health
        self.health_status = health_status


class Party():
    def __init__(self, name):
        self.party_name = name
        self.members = []

    def add(self, character: Character=None):
        assert character is not None, 'You must supply a character'
        self.members.append(character)


class Player(Model):

    class Meta:
        table_name = 'players'
        region = 'us-east-1'
        write_capacity_units = 1
        read_capacity_units = 1

    player_name = UnicodeAttribute(hash_key=True)
    character_name = UnicodeAttribute(range_key=True)
    character_initiative = NumberAttribute(default=0)
    rolled_initiative = NumberAttribute(default=0)
    created_datetime = UTCDateTimeAttribute(default=datetime.now())
    updated_datetime = UTCDateTimeAttribute(default=datetime.now())