from api import Api
import random as rnd
import json as js
with open("private.json", "r") as outfile:
    data = js.load(outfile)
TOKEN = data["TOKEN"]
USER = data["USER"]
HOME = data["HOME"]
PASSWORD = data["PASSWORD"]
ROOM = data["ROOM"]

a = Api(HOME, USER, TOKEN)
# me = a.whoami()
# a.send_text_message(ROOM, str(me))
a.send_text_message(ROOM, f"Random Number: {rnd.randint(0, 99999)}")
