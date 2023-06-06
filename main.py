from api import Api
import json as js
from nio import AsyncClientConfig
with open("private.json", "r") as outfile:
    data = js.load(outfile)
TOKEN: str = data["TOKEN"]
USER: str = data["USER"]
HOME: str = data["HOME"]
PASSWORD: str = data["PASSWORD"]
ROOM: str = data["ROOM"]
DEVICE: str = data["DEVICE"]
STORE: str = data["STORE"]
CONFIG = AsyncClientConfig(store_name="my_store", store_sync_tokens=True)

a = Api(HOME, USER, TOKEN, DEVICE, PASSWORD, ROOM, CONFIG, STORE)
