import nio
import json as js
import requests as rqs
import uuid

# TODO: Understand how Nio's Callbacks work. Own On Event Callback Implementation(If needed); Make 3 Different
#  files: api.py - API, which will do all stuff related to nio.Api; Bot which will do all stuff related to callbacks
#  and running bot; Plugins which will do all stuff related to Plugins; I need to make it work good - You can use API
#  functions without proving any Account data

# TODO: Port to nio.Client

class Api:

    def __init__(self, home: str, user: str, token: str):
        """
        Class: Api
        Wrapper around nio.Api class
        :param home: (string) URL of Home server
        :param user: (string) Matrix ID of user
        :param token: (string) Access Token
       """
        self.home = home
        self.user = user
        self.token = token

    def _exec(self, request: tuple[str, str], request_data: dict = None) -> dict:
        """
        Protected Class Method, Sends Request from tuple
        :param request: (tuple) Tuple of Request Type and URL
        :param request_data: (dictionary)(optional) Extra data, which is used for special requests
        :return: (dictionary) Returns Request's response
        """
        request_type, request_body = request
        if request_type in ("GET", "POST", "PUT", "DELETE", "PATCH"):
            method = getattr(rqs, request_type.lower())
            if request_data is None:
                response = method(f"{self.home}{request_body}").text
            else:
                response = method(f"{self.home}{request_body}", json=request_data).text
            return js.loads(response)

    def get_display_name(self) -> str:
        """
        High Level Wrapper around nio.Api.profile_get_displayname
        :return: (string) Display Name of User
        """
        request = nio.Api.profile_get_displayname(self.user, self.token)
        name = self._exec(request)
        return name["displayname"]

    def _send_event(self, event_type: str, room_id: str, body: dict) -> dict:
        """
        Low Level Wrapper around nio.Api.room_send
        :param event_type: (string) Event Type
        :param room_id: (string) Room ID
        :param body: (dictionary) Dictionary which contains message data
        :return: (dictionary) Event ID of Sent Message
        """
        request = nio.Api.room_send(self.token, room_id, event_type, body, str(uuid.uuid4()))
        request_query = request[0], request[1]
        request_data = body
        response = self._exec(request_query, request_data)
        return response

    def send_text_message(self, room_id: str, content: str) -> dict:
        """
        Method to send Text Message to room with specified ID
        :param room_id: (string) Room ID
        :param content: (string) Message Content
        :return: (dictionary) Event ID of sent message
        """
        return self._send_event("m.room.message", room_id, {"msgtype": "m.room.message", "body": content})

    def get_room_members(self, room_id: str) -> dict:
        """
        Method to view members of Specified room
        :param room_id: (string) Room ID
        :return: (dictionary) Dictionary of all members in specified room
        """
        request = nio.Api.joined_members(self.token, room_id)
        return self._exec(request)

    def whoami(self) -> dict:
        """
        Get Information about Token's owner
        :return: (dictionary) Information about Token's owner
        """
        request = nio.Api.whoami(self.token)
        return self._exec(request)
