"""Client to send OSC packets to an OSC server."""

import socket

class UDPClient(object):
  """OSC client to send OscMessages or OscBundles via UDP."""

  def __init__(self, address, port):
    self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self._sock.setblocking(0)
    self._address = address
    self._port = port

  def send(self, content):
    """Sends an OscBundle or OscMessage to the server."""
    self._sock.sendto(content.dgram, (self._address, self._port))
