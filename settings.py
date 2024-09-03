import json


SETTINGS = {}

with open('settings.json', encoding = "utf-8") as json_file:
    SETTINGS = json.load(json_file)
    
def updateSettings():
    with open('settings.json', encoding = "utf-8") as json_file:
        settings = json.load(json_file)
        return settings