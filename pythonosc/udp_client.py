"""UDP Clients for sending OSC messages to an OSC server"""

import sys

if sys.version_info > (3, 5):
    from collections.abc import Iterable
else:
    from collections import Iterable

import socket

from .osc_message_builder import OscMessageBuilder, ArgValue
from pythonosc.osc_message import OscMessage
from pythonosc.osc_bundle import OscBundle

from typing import Union

class UDPClient(object):
    """OSC client to send :class:`OscMessage` or :class:`OscBundle` via UDP"""

    def __init__(self, address: str, port: int, allow_broadcast: bool = False, force_ipv4 = False, force_ipv6 = False) -> None:
        """Initialize client

        As this is UDP it will not actually make any attempt to connect to the
        given server at ip:port until the send() method is called.

        Args:
            address: IP address of server
            port: Port of server
            allow_broadcast: Allow for broadcast transmissions
            force_ipv4: require that remote address is IPv4
            force_ipv6: require thta remote address is IPv6
        """

        if force_ipv4 and force_ipv6:
            raise ValueError("Can only force one of IPv4 or IPv6")
        elif force_ipv4:
            family = socket.AF_INET
        elif force_ipv6:
            family = socket.AF_INET6
        else:
            family = 0

        for addr in socket.getaddrinfo(address, port, type=socket.SOCK_DGRAM, family=family):
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


class SimpleUDPClient(UDPClient):
    """Simple OSC client that automatically builds :class:`OscMessage` from arguments"""

    def send_message(self, address: str, value: ArgValue) -> None:
        """Build :class:`OscMessage` from arguments and send to server

        Args:
            address: OSC address the message shall go to
            value: One or more arguments to be added to the message
        """
        builder = OscMessageBuilder(address=address)
        if value is None:
            values = []
        elif not isinstance(value, Iterable) or isinstance(value, (str, bytes)):
            values = [value]
        else:
            values = value
        for val in values:
            builder.add_arg(val)
        msg = builder.build()
        self.send(msg)
