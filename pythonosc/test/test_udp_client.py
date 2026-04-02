import unittest
from unittest import mock

from pythonosc import osc_message_builder
from pythonosc import udp_client


class TestUdpClient(unittest.TestCase):
    @mock.patch("socket.socket")
    def test_send(self, mock_socket_ctor):
        mock_socket = mock_socket_ctor.return_value
        client = udp_client.UDPClient("::1", 31337)

        msg = osc_message_builder.OscMessageBuilder("/").build()
        client.send(msg)

        self.assertTrue(mock_socket.sendto.called)
        mock_socket.sendto.assert_called_once_with(msg.dgram, ("::1", 31337))


class TestSimpleUdpClient(unittest.TestCase):
    def setUp(self):
        self.patcher = mock.patch("pythonosc.udp_client.OscMessageBuilder")
        self.patcher.start()
        self.builder = udp_client.OscMessageBuilder.return_value
        self.msg = self.builder.build.return_value
        self.client = mock.Mock()

    def tearDown(self):
        self.patcher.stop()

    def test_send_message_calls_send_with_msg(self):
        udp_client.SimpleUDPClient.send_message(self.client, "/address", 1)
        self.client.send.assert_called_once_with(self.msg)

    def test_send_message_calls_add_arg_with_value(self):
        udp_client.SimpleUDPClient.send_message(self.client, "/address", 1)
        self.builder.add_arg.assert_called_once_with(1)

    def test_send_message_calls_add_arg_once_with_string(self):
        udp_client.SimpleUDPClient.send_message(self.client, "/address", "hello")
        self.builder.add_arg.assert_called_once_with("hello")

    def test_send_message_calls_add_arg_multiple_times_with_list(self):
        udp_client.SimpleUDPClient.send_message(
            self.client, "/address", [1, "john", True]
        )
        self.assertEqual(self.builder.add_arg.call_count, 3)


class TestUdpClientClose(unittest.TestCase):
    @mock.patch("socket.socket")
    def test_close(self, mock_socket_ctor):
        mock_socket = mock_socket_ctor.return_value
        client = udp_client.UDPClient("::1", 31337)
        client.close()
        self.assertTrue(mock_socket.close.called)

    @mock.patch("socket.socket")
    def test_context_manager(self, mock_socket_ctor):
        mock_socket = mock_socket_ctor.return_value
        with udp_client.UDPClient("::1", 31337) as client:
            self.assertIsInstance(client, udp_client.UDPClient)
        self.assertTrue(mock_socket.close.called)


class TestUdpClientTimeout(unittest.TestCase):
    @mock.patch("socket.socket")
    def test_init_timeout(self, mock_socket_ctor):
        mock_socket = mock_socket_ctor.return_value
        client = udp_client.UDPClient("::1", 31337, timeout=10.0)
        self.assertEqual(client._timeout, 10.0)
        mock_socket.settimeout.assert_any_call(10.0)

    @mock.patch("socket.socket")
    def test_receive_default_timeout(self, mock_socket_ctor):
        mock_socket = mock_socket_ctor.return_value
        client = udp_client.UDPClient("::1", 31337, timeout=10.0)
        mock_socket.recv.return_value = b"data"
        client.receive()
        mock_socket.settimeout.assert_called_with(10.0)

    @mock.patch("socket.socket")
    def test_receive_override_timeout(self, mock_socket_ctor):
        mock_socket = mock_socket_ctor.return_value
        client = udp_client.UDPClient("::1", 31337, timeout=10.0)
        mock_socket.recv.return_value = b"data"
        client.receive(timeout=5.0)
        mock_socket.settimeout.assert_called_with(5.0)


if __name__ == "__main__":
    unittest.main()
