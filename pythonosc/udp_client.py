"""UDP Clients for sending OSC messages to an OSC server"""

import sys

if sys.version_info > (3, 5):
    from collections.abc import Iterable
else:
    from collections import Iterable

import socket
from typing import Generator, Union

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_bundle import OscBundle
from pythonosc.osc_message import OscMessage
from pythonosc.osc_message_builder import ArgValue, OscMessageBuilder


class UDPClient(object):
    """OSC client to send :class:`OscMessage` or :class:`OscBundle` via UDP"""

    def __init__(
        self,
        address: str,
        port: int,
        allow_broadcast: bool = False,
        family: socket.AddressFamily = socket.AF_UNSPEC,
    ) -> None:
        """Initialize client

        As this is UDP it will not actually make any attempt to connect to the
        given server at ip:port until the send() method is called.

        Args:
            address: IP address of server
            port: Port of server
            allow_broadcast: Allow for broadcast transmissions
            family: address family parameter (passed to socket.getaddrinfo)
        """

        for addr in socket.getaddrinfo(
            address, port, type=socket.SOCK_DGRAM, family=family
        ):
            af, socktype, protocol, canonname, sa = addr

            try:
                self._sock = socket.socket(af, socktype)
            except OSError:
                continue
            break

        self._sock.setblocking(False)
        if allow_broadcast:
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._address = address
        self._port = port

    def send(self, content: Union[OscMessage, OscBundle]) -> None:
        """Sends an :class:`OscMessage` or :class:`OscBundle` via UDP

        Args:
            content: Message or bundle to be sent
        """
        self._sock.sendto(content.dgram, (self._address, self._port))

    def receive(self, timeout: int = 30) -> bytes:
        """Wait :int:`timeout` seconds for a message an return the raw bytes

        Args:
            timeout: Number of seconds to wait for a message
        """
        self._sock.settimeout(timeout)
        try:
            return self._sock.recv(4096)
        except TimeoutError:
            return b""


class SimpleUDPClient(UDPClient):
    """Simple OSC client that automatically builds :class:`OscMessage` from arguments"""

    def send_message(self, address: str, value: ArgValue) -> None:
        """Build :class:`OscMessage` from arguments and send to server

        Args:
            address: OSC address the message shall go to
            value: One or more arguments to be added to the message
        """
        builder = OscMessageBuilder(address=address)
        values: ArgValue
        if value is None:
            pass
        elif not isinstance(value, Iterable) or isinstance(value, (str, bytes)):
            builder.add_arg(value)
        else:
            for val in value:
                builder.add_arg(val)
        msg = builder.build()
        self.send(msg)

    def get_messages(self, timeout: int = 30) -> Generator:
        """Wait :int:`timeout` seconds for a message from the server and convert it to a :class:`OscMessage`

        Args:
            timeout: Time in seconds to wait for a message
        """
        msg = self.receive(timeout)
        while msg:
            yield OscMessage(msg)
            msg = self.receive(timeout)


class DispatchClient(SimpleUDPClient):
    """OSC Client that includes a :class:`Dispatcher` for handling responses and other messages from the server"""

    dispatcher = Dispatcher()

    def handle_messages(self, timeout: int = 30) -> None:
        """Wait :int:`timeout` seconds for a message from the server and process each message with the registered
        handlers.  Continue until a timeout occurs.

        Args:
            timeout: Time in seconds to wait for a message
        """
        msg = self.receive(timeout)
        while msg:
            self.dispatcher.call_handlers_for_packet(msg, (self._address, self._port))
            msg = self.receive(timeout)
