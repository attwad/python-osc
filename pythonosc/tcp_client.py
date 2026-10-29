"""TCP Clients for sending OSC messages to an OSC server"""

import asyncio
import socket
from contextlib import suppress
from typing import Any, AsyncGenerator, Awaitable, Generator, Iterable, List, Union

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_bundle import OscBundle
from pythonosc.osc_message import OscMessage
from pythonosc.osc_message_builder import ArgValue, build_msg
from pythonosc.osc_tcp_server import MODE_1_1, get_framing
from pythonosc.parsing.framing import FramingParser


class TCPClient:
    """OSC client to send :class:`OscMessage` or :class:`OscBundle` via TCP"""

    def __init__(
        self,
        address: str,
        port: int,
        family: socket.AddressFamily = socket.AF_INET,
        mode: str = MODE_1_1,
        timeout: float | None = 30.0,
    ) -> None:
        """Initialize client

        Args:
            address: IP address of server
            port: Port of server
            family: address family parameter (passed to socket.getaddrinfo)
            timeout: Default timeout in seconds for socket operations
        """

        self.address = address
        self.port = port
        self.family = family
        self._timeout = timeout
        self._framing = get_framing(mode)
        self._parser = FramingParser(self._framing)
        self.socket = socket.socket(self.family, socket.SOCK_STREAM)
        self.socket.settimeout(timeout)
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
        self.socket.sendall(self._framing.encode(content.dgram))

    def receive(self, timeout: float | None = None) -> List[bytes]:
        messages = []
        effective_timeout = timeout if timeout is not None else self._timeout
        self.socket.settimeout(effective_timeout)

        with suppress(TimeoutError):
            while chunk := self.socket.recv(16384):
                messages.extend(self._parser.feed(chunk))

        return messages

    def close(self):
        self._parser.reset()
        self.socket.close()


class SimpleTCPClient(TCPClient):
    """Simple OSC client that automatically builds :class:`OscMessage` from arguments"""

    def send_message(
        self, address: str, value: Union[ArgValue, Iterable[ArgValue]] = ()
    ) -> None:
        """Build :class:`OscMessage` from arguments and send to server

        Args:
            address: OSC address the message shall go to
            value: One or more arguments to be added to the message. Omit for
                no arguments; an empty string is a string argument.
        """
        msg = build_msg(address, value)
        return self.send(msg)

    def get_messages(self, timeout: float | None = None) -> Generator:
        r = self.receive(timeout)
        while r:
            for m in r:
                yield OscMessage(m)
            r = self.receive(timeout)


class TCPDispatchClient(SimpleTCPClient):
    """OSC TCP Client that includes a :class:`Dispatcher` for handling responses and other messages from the server"""

    def __init__(self, *args: Any, dispatcher: Dispatcher | None = None, **kwargs: Any):
        self.dispatcher = dispatcher or Dispatcher()
        super().__init__(*args, **kwargs)

    def handle_messages(self, timeout_sec: float | None = None) -> None:
        """Wait :int:`timeout` seconds for a message from the server and process each message with the registered
        handlers.  Continue until a timeout occurs.

        Args:
            timeout: Time in seconds to wait for a message
        """
        r = self.receive(timeout_sec)
        while r:
            for m in r:
                self.dispatcher.call_handlers_for_packet(m, (self.address, self.port))
            r = self.receive(timeout_sec)


class AsyncTCPClient:
    """Async OSC client to send :class:`OscMessage` or :class:`OscBundle` via TCP"""

    def __init__(
        self,
        address: str,
        port: int,
        family: socket.AddressFamily = socket.AF_INET,
        mode: str = MODE_1_1,
        timeout: float | None = 30.0,
    ) -> None:
        """Initialize client

        Args:
            address: IP address of server
            port: Port of server
            family: address family parameter (passed to socket.getaddrinfo)
            timeout: Default timeout in seconds for socket operations
        """
        self.address: str = address
        self.port: int = port
        self.family: socket.AddressFamily = family
        self._timeout = timeout
        self._framing = get_framing(mode)
        self._parser = FramingParser(self._framing)

    async def __aenter__(self):
        await self.__open__()
        return self

    async def __open__(self):
        self.reader, self.writer = await asyncio.open_connection(
            self.address, self.port
        )

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def send(self, content: Union[OscMessage, OscBundle]) -> Awaitable[None]:
        """Sends an :class:`OscMessage` or :class:`OscBundle` via TCP

        Args:
            content: Message or bundle to be sent
        """
        self.writer.write(self._framing.encode(content.dgram))
        return self.writer.drain()

    def _read_with_timeout(self, timeout: float | None) -> Awaitable[bytes]:
        return asyncio.wait_for(self.reader.read(16384), timeout)

    async def receive(self, timeout: float | None = None) -> List[bytes]:
        messages = []
        effective_timeout = timeout if timeout is not None else self._timeout

        with suppress(TimeoutError):
            while chunk := await self._read_with_timeout(effective_timeout):
                messages.extend(self._parser.feed(chunk))

        return messages

    def close(self) -> Awaitable[None]:
        self._parser.reset()
        self.writer.write_eof()
        self.writer.close()
        return self.writer.wait_closed()


class AsyncSimpleTCPClient(AsyncTCPClient):
    """Simple OSC client that automatically builds :class:`OscMessage` from arguments"""

    async def send_message(
        self, address: str, value: Union[ArgValue, Iterable[ArgValue]] = ()
    ) -> None:
        """Build :class:`OscMessage` from arguments and send to server

        Args:
            address: OSC address the message shall go to
            value: One or more arguments to be added to the message. Omit for
                no arguments; an empty string is a string argument.
        """
        msg = build_msg(address, value)
        return await self.send(msg)

    async def get_messages(self, timeout: float | None = None) -> AsyncGenerator:
        r = await self.receive(timeout)
        while r:
            for m in r:
                yield OscMessage(m)
            r = await self.receive(timeout)


class AsyncDispatchTCPClient(AsyncTCPClient):
    """OSC Client that includes a :class:`Dispatcher` for handling responses and other messages from the server"""

    def __init__(self, *args: Any, dispatcher: Dispatcher | None = None, **kwargs: Any):
        self.dispatcher = dispatcher or Dispatcher()
        super().__init__(*args, **kwargs)

    async def handle_messages(self, timeout: float | None = None) -> None:
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
