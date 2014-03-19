import socket
import unittest
from unittest import mock

from pythonosc import osc_message_builder
from pythonosc import udp_client


class TestUdpClient(unittest.TestCase):

  @mock.patch('socket.socket')
  def test_send(self, mock_socket_ctor):
    mock_socket = mock_socket_ctor.return_value
    client = udp_client.UDPClient('::1', 31337)

    msg = osc_message_builder.OscMessageBuilder('/').build()
    client.send(msg)

    self.assertTrue(mock_socket.sendto.called)
    mock_socket.sendto.assert_called_once_with(msg.dgram, ('::1', 31337))


if __name__ == "__main__":
  unittest.main()
