from neutrino_cli.compiler.templates.template import Template


template = '''
import json
from typing import Any, Optional

from fastapi import WebSocket


class ConnectionManager:
    """
    Manages WebSocket connections for rooms and individual clients.
    """
    def __init__(self):
        # Key: room_id, Value: Dict of client_id to WebSocket
        self.room_connections: dict[str, dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str = None, client_id: str = None) -> None:
        """
        Connects a client to a room.

        Parameters:
            websocket (WebSocket): The WebSocket connection.
            room_id (str, optional): The ID of the room to join. Defaults to 'default'.
            client_id (str, optional): The ID of the client. Defaults to ''.
        """
        if room_id is None:
            room_id = 'default'
        if client_id is None:
            client_id = '0'
            
        await websocket.accept()
        if room_id not in self.room_connections:
            self.room_connections[room_id] = {}
        self.room_connections[room_id][client_id] = websocket

    def disconnect(self, websocket: WebSocket, room_id: str = 'default') -> None:
        """
        Disconnects a client from a room.

        Parameters:
            websocket (WebSocket): The WebSocket connection.
            room_id (str, optional): The ID of the room to leave. Defaults to 'default'.
        """
        room = self.room_connections.get(room_id, {})
        client_id = next((k for k, v in room.items() if v == websocket), None)
        if client_id is not None:
            room.pop(client_id)

    async def send_message(self, message: str, room_id: str = 'default', client_id: str = None) -> None:
        """
        Sends a message to a specific room or client.

        Parameters:
            message (str): The message to send.
            room_id (str, optional): The ID of the room. Defaults to 'default'.
            client_id (str, optional): The ID of the client. If None, broadcasts to the room. Defaults to None.
        """
        room = self.room_connections.get(room_id, {})
        if client_id:
            websocket = room.get(client_id)
            if websocket:
                await websocket.send_text(message)
        else:
            for websocket in room.values():
                await websocket.send_text(message)

    async def broadcast_all(self, message: str) -> None:
        """
        Broadcasts a message to all rooms and clients.

        Parameters:
            message (str): The message to broadcast.
        """
        for room in self.room_connections.values():
            for websocket in room.values():
                await websocket.send_text(message)
                
    async def handle_error(self, websocket: WebSocket, e: Exception) -> None:
        """
        Handles errors by sending a specific status code and optional message.

        Parameters:
            websocket (WebSocket): The WebSocket connection.
            status_code (int): The status code to close the connection with.
            message (str, optional): Optional message to send before closing. Defaults to None.
        """
        message = e.message if hasattr(e, 'message') else str(e)
        status_code = e.status_code if hasattr(e, 'status_code') else 1007

        await websocket.send_text(message)
        await websocket.close(code=status_code)

    async def parse_and_send_message(self, message: Any) -> None:
        """
        Parses the message structure and sends the message accordingly.

        Parameters:
            message (Any): The message which could be a simple value, or a tuple (data, target)
        """
        if isinstance(message, tuple) and len(message) == 2:
            data, target = message
            json_data = json.dumps(data)

            if isinstance(target, (str, int)):
                await self.send_message(json_data, client_id=str(target))
            elif isinstance(target, dict):
                client_id = target.get('client_id', None)
                room_id = target.get('room_id', None)

                if client_id and room_id:
                    await self.send_message(json_data, room_id, client_id)
                elif room_id:
                    await self.send_message(json_data, room_id)
                elif client_id:
                    await self.send_message(json_data, client_id=client_id)
        else:
            await self.broadcast_all(json.dumps(message))
        
        
manager: ConnectionManager = ConnectionManager()

'''


class WebsocketsManagerTemplate(Template):
    def __init__(self):
        template_vars = {}
        super().__init__(template_str=template, template_vars=template_vars, is_python=True)

