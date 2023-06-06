import nio
import asyncio as aio
from uuid import uuid4
from random import randint


# TODO Make 3 Different files: api.py - API, which will do all stuff related to nio.Api; Bot which will do all stuff
#  related to callbacks and running bot; Plugins which will do all stuff related to Plugins; I need to make it work
#  good - You can use API functions without proving any Account data
# TODO: Port to nio.Client

class NioRoomsNotFound(ValueError):
    pass


class Api:

    def __init__(self, home: str, user: str, token: str, device_id: str,
                 password: str, room: str, client_config: nio.AsyncClientConfig = None, store_path: str = "") -> None:
        """
        Class: Api
        Wrapper around nio.Client class
        :param home: (string) URL of Home server
        :param user: (string) Matrix ID of user
        :param token: (string) Access Token
        :param device_id: (string) Device ID
        :param password: (string) User's Password
        :param room: (string) Room ID
        :param client_config: (AsyncClientConfig) Client Configuration
        :param store_path: (string) Path to directory which be used for storing State Storage
       """
        self.home = home
        self.user = user
        self.token = token
        self.device_id = device_id
        self.password = password
        self.room = room
        self.client_config = client_config
        self.store_path = store_path

        if self.client_config:
            self.client = nio.AsyncClient(self.home, self.user, self.device_id, config=self.client_config,
                                          store_path=self.store_path)
        else:
            self.client = nio.AsyncClient(self.home, self.user, self.device_id, store_path=self.store_path)

        loop = aio.get_event_loop()
        bot = loop.run_until_complete(self.client.login(password=self.password))
        print(bot)
        join_sync = loop.run_until_complete(self.client.join(self.room))
        sync = loop.run_until_complete(self.client.sync(timeout=3000))
        messages = loop.run_until_complete(self.client.room_messages(self.room, sync.next_batch))
        print(messages)
        print(f".:{self.client.rooms}")
        if not self.client.rooms:
            raise NioRoomsNotFound("Rooms not Found!")
        loop.run_until_complete(self.client.room_send(self.room, "m.room.message",
                                                      {
                                                          "msgtype": "m.text",
                                                          "body": f"Random Number(Encrypted): {randint(0, 99999)}"
                                                      }, str(uuid4()), ignore_unverified_devices=False
                                                      ))
        loop.run_until_complete(aio.sleep(15))
        loop.run_until_complete(self.client.close())
