import nio
import asyncio as aio
from uuid import uuid4
from PIL import Image
from pymediainfo import MediaInfo
import aiofiles  # TODO: Optimize this Import
import aiofiles.os
import os
from magic import Magic
import aiohttp
from io import BytesIO
from validators import url as is_url
from pathlib import Path

# TODO: Sort Imports
# TODO Make 3 Different files: api.py - API, which will do all stuff related to nio.Api; Bot which will do all stuff
#   related to callbacks and running bot; Plugins which will do all stuff related to Plugins


class NioRoomsNotFound(ValueError):
    pass


class Api:

    def __init__(self, home: str, user: str, token: str, device_id: str,
                 password: str, room: str, client_config: nio.AsyncClientConfig = None, store_path: str = "") -> None:
        """
        Class: Api
        Wrapper around nio.AsyncClient class
        :param home: (string) URL of Home server
        :param user: (string) Matrix ID of user
        :param token: (string) Access Token
        :param device_id: (string) Device ID
        :param password: (string) User's Password
        :param room: (string) Room ID
        :param client_config: (AsyncClientConfig) Client Configuration
        :param store_path: (string) Path to directory which be used for storing State Storage
        :return: (None)
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

        self.loop = aio.get_event_loop()
        bot = self.loop.run_until_complete(self.client.login(password=self.password))
        print(bot)
        join_sync = self.loop.run_until_complete(self.client.join(self.room))
        sync = self.loop.run_until_complete(self.client.sync(timeout=3000))
        messages = self.loop.run_until_complete(self.client.room_messages(self.room, sync.next_batch))
        print(messages)
        print(f".:{self.client.rooms}")
        if not self.client.rooms:
            self.loop.run_until_complete(self.close())
            raise NioRoomsNotFound("Rooms not Found!")
        self.loop.run_until_complete(aio.sleep(15))
        self.loop.run_until_complete(self.client.close())

    async def send_text_message(self, room_id: str, message: str) -> None:
        """
        :param room_id: (string) Room ID
        :param message: (string) Message Content
        :return: (None)
        """
        await self.client.room_send(room_id, "m.room.message", {"msgtype": "m.text", "body": message}, str(uuid4()),
                                    ignore_unverified_devices=False)

    @staticmethod
    async def get_network_file(url: str) -> tuple[BytesIO, str, int, str]:
        """
        Used to get file, and it's info from Internet
        :param url: (string) URL to File
        :return: (tuple) BytesIO object, File Name (string), File Name (string), File Size (string), MIME Type (string)
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as file:
                mime = file.headers.get("Content-Type")
                size = file.headers.get("Content-Length", "0")
                file_bytes = BytesIO(await file.read())
                name = os.path.basename(url)
                return file_bytes, name, int(size), mime

    @staticmethod
    async def get_local_file(file: str) -> tuple[BytesIO, str, int, str]:
        """
        Used to get file, and it's info from Internet
        :param file: (string) URL to File
        :return: (tuple) AsyncBufferedReader file, File Name (string), File Name (string), Size (string), MIME (string)
        """
        async with aiofiles.open(file, "rb") as outfile:
            name = os.path.basename(file)
            stat = await aiofiles.os.stat(file)
            size = stat.st_size
            mime = Magic(mime=True).from_file(file)
            out = BytesIO(await outfile.read())
            return out, name, size, mime

    async def send_file(self,
                        room_id: str,
                        file: str | tuple[bytes, str, int, str] | list[bytes, str, int, str],
                        message_type: str = "m.file",
                        extra_content: dict = None,
                        body: str = None,
                        validate_mime: str = None) -> None:
        """
        Method to send file to room
        :param room_id: (string) Room ID
        :param file: (string)/(tuple) Path/URL to file/Tuple with BytesIO, Name, Size and MIME
        :param message_type: (string) Type of message, m.file by default
        :param extra_content: (dictionary) Additional Information for content
        :param body: (string) Body of Message
        :param validate_mime: (string) MIME type to compare with file's MIME
        :return: (None)
        """
        if isinstance(file, (tuple, list)):
            byte, name, size, mime = file
            out = BytesIO(byte)
        elif is_url(file):
            out, name, size, mime = await self.get_network_file(file)
        elif Path(file).exists():
            out, name, size, mime = await self.get_local_file(file)
        else:
            raise ValueError("File not found")

        if validate_mime is not None:
            assert mime.startswith(validate_mime), f"Got MIME Type {mime}, but expected {validate_mime}"

        if body is None and not isinstance(body, str):
            body = name

        response, keys = await self.client.upload(out,
                                                  content_type=mime,
                                                  filename=name,
                                                  filesize=size)
        if not isinstance(response, nio.UploadResponse):
            raise TypeError(f"Uploading failed. Expected UploadResponse, but got {type(response)}")
        content = {
            "msgtype": message_type,
            "body": body,
            "url": response.content_uri,
            "info": {
                "size": size,
                "mimetype": mime
            }
        }
        if extra_content is not None:
            content.update(extra_content)

        await self.client.room_send(room_id, "m.room.message", content=content)

    async def send_image(self, room_id: str, image_path: str, body: str = None) -> None:
        """
        Method to send an Image to room
        :param room_id: (string) Room ID
        :param image_path: (string) Path/URL to image
        :param body: (string) Optional, Message Body
        :return: (None)
        """
        if is_url(image_path):
            result = await self.get_network_file(image_path)
        elif Path(image_path).exists():
            result = await self.get_local_file(image_path)
        else:
            raise ValueError("File not found")
        image = Image.open(result[0])
        width, height = image.size
        content = {
            "info": {
                "thumbnail_info": None,
                "w": width,
                "h": height,
                "thumbnail_url": None
                }
            }
        out, name, size, mime = result
        file = (out.getvalue(), name, size, mime)
        await self.send_file(room_id, file,
                             message_type="m.image",
                             extra_content=content,
                             validate_mime="image/",
                             body=body)

    async def send_audio(self, room_id: str, audio_path: str, body: str = None) -> None:
        """
        Method to send an Audio to room
        :param room_id: (string) Room ID
        :param audio_path: (string) Path/URL to audio
        :param body: (string) Optional, Message Body
        :return: (None)
        """
        if is_url(audio_path):
            result = await self.get_network_file(audio_path)
        elif Path(audio_path).exists():
            result = await self.get_local_file(audio_path)
        else:
            raise ValueError("File not found")
        out, name, size, mime = result
        file = (out.getvalue(), name, size, mime)
        await self.send_file(room_id, file,
                             message_type="m.audio",
                             validate_mime="audio/",
                             body=body)

    async def send_video(self, room_id: str, video_path: str, body: str = None) -> None:
        """
        Method to send a video to room
        :param room_id: (string) Room ID
        :param video_path: (string) Path/URL to video
        :param body: (string) Optional, Message Body
        :return: (None)
        """
        if is_url(video_path):
            result = await self.get_network_file(video_path)
        elif Path(video_path).exists():
            result = await self.get_local_file(video_path)
        else:
            raise ValueError("File not found")
        out, name, size, mime = result
        video = MediaInfo.parse(out)
        width = height = None
        for track in video.tracks:
            if track.track_type == "Video":
                width, height = track.width, track.height

        if (width is None) or (height is None):
            raise ValueError("Can't get Width/Height of Video")

        content = {
            "info": {
                "thumbnail_info": {
                    "w": width / 100 * 62.5,
                    "h": height / 100 * 62.5
                },
            },
            "w": width,
            "h": height
        }

        file = (out.getvalue(), name, size, mime)
        await self.send_file(room_id, file,
                             message_type="m.video",
                             validate_mime="video/",
                             extra_content=content,
                             body=body)

    async def close(self) -> None:
        await self.client.close()
