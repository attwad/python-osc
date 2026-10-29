"""Empty strings are arguments; omitted values and empty iterables are not."""

import unittest
from typing import Iterable
from unittest import mock

from pythonosc import tcp_client, udp_client
from pythonosc.osc_message_builder import ArgValue, build_msg
from pythonosc.parsing import slip

EMPTY_STRING_DGRAM = b"/v\x00\x00,s\x00\x00\x00\x00\x00\x00"
NO_ARGUMENTS_DGRAM = b"/v\x00\x00,\x00\x00\x00"


class TestEmptyStringBuilder(unittest.TestCase):
    def test_explicit_empty_string(self) -> None:
        message = build_msg("/v", "")
        self.assertEqual(message.params, [""])
        self.assertEqual(message.dgram, EMPTY_STRING_DGRAM)

    def test_omitted_and_empty_iterable_values(self) -> None:
        self.assertEqual(build_msg("/v").dgram, NO_ARGUMENTS_DGRAM)
        empty_values: list[Iterable[ArgValue]] = [[], (), iter(())]
        for value in empty_values:
            with self.subTest(value=value):
                self.assertEqual(build_msg("/v", value).dgram, NO_ARGUMENTS_DGRAM)

    def test_other_scalar_values_and_iterables(self) -> None:
        values: list[ArgValue] = [0, False, None, "hello"]
        for value in values:
            with self.subTest(value=value):
                self.assertEqual(build_msg("/v", value).params, [value])
        self.assertEqual(build_msg("/v", [""]).dgram, EMPTY_STRING_DGRAM)
        nested_values: list[ArgValue] = [0, "", None]
        self.assertEqual(build_msg("/v", iter(nested_values)).params, nested_values)


class TestEmptyStringTcpClient(unittest.TestCase):
    @mock.patch("socket.socket")
    def test_explicit_empty_string(self, socket_factory: mock.Mock) -> None:
        with tcp_client.SimpleTCPClient("127.0.0.1", 31337) as client:
            client.send_message("/v", "")
        socket_factory.return_value.sendall.assert_called_once_with(
            slip.encode(EMPTY_STRING_DGRAM)
        )

    @mock.patch("socket.socket")
    def test_omitted_value(self, socket_factory: mock.Mock) -> None:
        with tcp_client.SimpleTCPClient("127.0.0.1", 31337) as client:
            client.send_message("/v")
        socket_factory.return_value.sendall.assert_called_once_with(
            slip.encode(NO_ARGUMENTS_DGRAM)
        )


class TestEmptyStringAsyncTcpClient(unittest.IsolatedAsyncioTestCase):
    def configure_connection(self, connection: mock.AsyncMock) -> mock.Mock:
        writer = mock.Mock()
        writer.drain = mock.AsyncMock()
        writer.wait_closed = mock.AsyncMock()
        connection.return_value = (mock.Mock(), writer)
        return writer

    @mock.patch("asyncio.open_connection")
    async def test_explicit_empty_string(self, connection: mock.AsyncMock) -> None:
        writer = self.configure_connection(connection)
        async with tcp_client.AsyncSimpleTCPClient("127.0.0.1", 31337) as client:
            await client.send_message("/v", "")
        writer.write.assert_called_once_with(slip.encode(EMPTY_STRING_DGRAM))

    @mock.patch("asyncio.open_connection")
    async def test_omitted_value(self, connection: mock.AsyncMock) -> None:
        writer = self.configure_connection(connection)
        async with tcp_client.AsyncSimpleTCPClient("127.0.0.1", 31337) as client:
            await client.send_message("/v")
        writer.write.assert_called_once_with(slip.encode(NO_ARGUMENTS_DGRAM))


class TestEmptyStringUdpClient(unittest.TestCase):
    @mock.patch("socket.socket")
    def test_existing_empty_string_behavior(self, socket_factory: mock.Mock) -> None:
        client = udp_client.SimpleUDPClient("127.0.0.1", 31337)
        with client:
            client.send_message("/v", "")
        socket_factory.return_value.sendto.assert_called_once_with(
            EMPTY_STRING_DGRAM, ("127.0.0.1", 31337)
        )
