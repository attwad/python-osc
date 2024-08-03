import asyncio
import unittest
from unittest import mock

from pythonosc import osc_message_builder, slip, tcp_client


class TestTcpClient(unittest.TestCase):
    @mock.patch("socket.socket")
    def test_client(self, mock_socket_ctor):
        mock_socket = mock_socket_ctor.return_value
        mock_send = mock.Mock()
        mock_recv = mock.Mock()
        mock_send.return_value = None
        mock_recv.return_value = ""

        mock_socket.sendall = mock_send
        mock_socket.recv = mock_recv
        msg = osc_message_builder.OscMessageBuilder("/").build()
        with tcp_client.TCPClient("::1", 31337) as client:
            client.send(msg)
        mock_socket.sendall.assert_called_once_with(slip.encode(msg.dgram))

    @mock.patch("socket.socket")
    def test_simple_client(self, mock_socket_ctor):
        mock_socket = mock_socket_ctor.return_value
        mock_send = mock.Mock()
        mock_recv = mock.Mock()
        mock_send.return_value = None
        mock_recv.return_value = ""

        mock_socket.sendall = mock_send
        mock_socket.recv = mock_recv
        with tcp_client.SimpleTCPClient("::1", 31337) as client:
            client.send_message("/", [])
        mock_socket.sendall.assert_called_once()


class TestAsyncTcpClient(unittest.IsolatedAsyncioTestCase):
    @mock.patch("asyncio.open_connection")
    async def test_send(self, mock_socket_ctor):
        mock_reader = mock.Mock()
        mock_writer = mock.Mock()
        mock_writer.drain = mock.AsyncMock()
        mock_writer.wait_closed = mock.AsyncMock()
        mock_socket_ctor.return_value = (mock_reader, mock_writer)
        loop = asyncio.get_running_loop()
        loop.set_debug(False)
        msg = osc_message_builder.OscMessageBuilder("/").build()
        async with tcp_client.AsyncTCPClient("::1", 31337) as client:
            await client.send(msg)

        self.assertTrue(mock_writer.write.called)
        mock_writer.write.assert_called_once_with(slip.encode(msg.dgram))

    @mock.patch("asyncio.open_connection")
    async def test_send_message_calls_send_with_msg(self, mock_socket_ctor):
        mock_reader = mock.Mock()
        mock_writer = mock.Mock()
        mock_writer.drain = mock.AsyncMock()
        mock_writer.wait_closed = mock.AsyncMock()
        mock_socket_ctor.return_value = (mock_reader, mock_writer)
        async with tcp_client.AsyncSimpleTCPClient("::1", 31337) as client:
            await client.send_message("/address", 1)
        self.assertTrue(mock_writer.write.called)


if __name__ == "__main__":
    unittest.main()
