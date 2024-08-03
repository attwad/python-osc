"""TCP Clients for sending OSC messages to an OSC server"""

import asyncio
import socket
import struct
from typing import AsyncGenerator, Generator, List, Union

from pythonosc import slip
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_bundle import OscBundle
from pythonosc.osc_message import OscMessage
from pythonosc.osc_message_builder import ArgValue, build_msg
from pythonosc.osc_tcp_server import MODE_1_1


class TCPClient(object):
    """Async OSC client to send :class:`OscMessage` or :class:`OscBundle` via TCP"""

    def __init__(
        self,
        address: str,
        port: int,
        family: socket.AddressFamily = socket.AF_INET,
        mode: str = MODE_1_1,
    ) -> None:
        """Initialize client

        Args:
            address: IP address of server
            port: Port of server
            family: address family parameter (passed to socket.getaddrinfo)
        """
        self.address = address
        self.port = port
        self.family = family
        self.mode = mode
        self.socket = socket.socket(self.family, socket.SOCK_STREAM)
        self.socket.settimeout(30)
        self.socket.connect((address, port))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def send(self, content: Union[OscMessage, OscBundle]) -> None:
        """Sends an :class:`OscMessage` or :class:`OscBundle` via TCP

        Args:
            content: Message or bundle to be sent
        """
        if self.mode == MODE_1_1:
            self.socket.sendall(slip.encode(content.dgram))
        else:
            b = struct.pack("!I", len(content.dgram))
            self.socket.sendall(b + content.dgram)

    def receive(self, timeout: int = 30) -> List[bytes]:
        self.socket.settimeout(timeout)
        if self.mode == MODE_1_1:
            try:
                buf = self.socket.recv(4096)
            except TimeoutError:
                return []
            if not buf:
                return []
            # If the last byte is not an END marker there could be more data coming
            while buf[-1] != 192:
                try:
                    newbuf = self.socket.recv(4096)
                except TimeoutError:
                    break
                if not newbuf:
                    # Maybe should raise an exception here?
                    break
                buf += newbuf
            return [slip.decode(p) for p in buf.split(slip.END_END)]
        else:
            buf = b""
            try:
                lengthbuf = self.socket.recv(4)
            except TimeoutError:
                return []
            (length,) = struct.unpack("!I", lengthbuf)
            while length > 0:
                try:
                    newbuf = self.socket.recv(length)
                except TimeoutError:
                    return []
                if not newbuf:
                    return []
                buf += newbuf
                length -= len(newbuf)
            return [buf]

    def close(self):
        self.socket.close()


class SimpleTCPClient(TCPClient):
    """Simple OSC client that automatically builds :class:`OscMessage` from arguments"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def send_message(self, address: str, value: ArgValue = "") -> None:
        """Build :class:`OscMessage` from arguments and send to server

        Args:
            address: OSC address the message shall go to
            value: One or more arguments to be added to the message
        """
        msg = build_msg(address, value)
        return self.send(msg)

    def get_messages(self, timeout: int = 30) -> Generator:
        r = self.receive(timeout)
        while r:
            for m in r:
                yield OscMessage(m)
            r = self.receive(timeout)


class AsyncTCPClient:
    """Async OSC client to send :class:`OscMessage` or :class:`OscBundle` via TCP"""

    def __init__(
        self,
        address: str,
        port: int,
        family: socket.AddressFamily = socket.AF_INET,
        mode: str = MODE_1_1,
    ) -> None:
        """Initialize client

        Args:
            address: IP address of server
            port: Port of server
            family: address family parameter (passed to socket.getaddrinfo)
        """
        self.address: str = address
        self.port: int = port
        self.mode: str = mode
        self.family: socket.AddressFamily = family

    def __await__(self):
        async def closure():
            await self.__open__()
            return self

        return closure().__await__()

    async def __aenter__(self):
        await self.__open__()
        return self

    async def __open__(self):
        self.reader, self.writer = await asyncio.open_connection(
            self.address, self.port
        )

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def send(self, content: Union[OscMessage, OscBundle]) -> None:
        """Sends an :class:`OscMessage` or :class:`OscBundle` via TCP

        Args:
            content: Message or bundle to be sent
        """
        if self.mode == MODE_1_1:
            self.writer.write(slip.encode(content.dgram))
        else:
            b = struct.pack("!I", len(content.dgram))
            self.writer.write(b + content.dgram)
        await self.writer.drain()

    async def receive(self, timeout: int = 30) -> List[bytes]:
        if self.mode == MODE_1_1:
            try:
                buf = await asyncio.wait_for(self.reader.read(4096), timeout)
            except TimeoutError:
                return []
            if not buf:
                return []
            # If the last byte is not an END marker there could be more data coming
            while buf[-1] != 192:
                try:
                    newbuf = await asyncio.wait_for(self.reader.read(4096), timeout)
                except TimeoutError:
                    break
                if not newbuf:
                    # Maybe should raise an exception here?
                    break
                buf += newbuf
            return [slip.decode(p) for p in buf.split(slip.END_END)]
        else:
            buf = b""
            try:
                lengthbuf = await asyncio.wait_for(self.reader.read(4), timeout)
            except TimeoutError:
                return []

            (length,) = struct.unpack("!I", lengthbuf)
            while length > 0:
                try:
                    newbuf = await asyncio.wait_for(self.reader.read(length), timeout)
                except TimeoutError:
                    return []
                if not newbuf:
                    return []
                buf += newbuf
                length -= len(newbuf)
            return [buf]

    async def close(self):
        self.writer.write_eof()
        self.writer.close()
        await self.writer.wait_closed()


class AsyncSimpleTCPClient(AsyncTCPClient):
    """Simple OSC client that automatically builds :class:`OscMessage` from arguments"""

    def __init__(
        self,
        address: str,
        port: int,
        family: socket.AddressFamily = socket.AF_INET,
        mode: str = MODE_1_1,
    ):
        super().__init__(address, port, family, mode)

    async def send_message(self, address: str, value: ArgValue = "") -> None:
        """Build :class:`OscMessage` from arguments and send to server

        Args:
            address: OSC address the message shall go to
            value: One or more arguments to be added to the message
        """
        msg = build_msg(address, value)
        return await self.send(msg)

    async def get_messages(self, timeout: int = 30) -> AsyncGenerator:
        r = await self.receive(timeout)
        while r:
            for m in r:
                yield OscMessage(m)
            r = await self.receive(timeout)


class AsyncDispatchTCPClient(AsyncTCPClient):
    """OSC Client that includes a :class:`Dispatcher` for handling responses and other messages from the server"""

    dispatcher = Dispatcher()

    async def handle_messages(self, timeout: int = 30) -> None:
        """Wait :int:`timeout` seconds for a message from the server and process each message with the registered
        handlers.  Continue until a timeout occurs.

        Args:
            timeout: Time in seconds to wait for a message
        """
        msgs = await self.receive(timeout)
        while msgs:
            for m in msgs:
                await self.dispatcher.async_call_handlers_for_packet(
                    m, (self.address, self.port)
                )
            msgs = await self.receive(timeout)
