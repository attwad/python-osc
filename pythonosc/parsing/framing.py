"""OSC message codecs for different framing strategies."""

from abc import ABCMeta, abstractmethod
from struct import pack, unpack_from

from pythonosc.parsing.slip import (
    END,
    decode as slip_decode,
    encode as slip_encode,
)


class Framing(metaclass=ABCMeta):
    """Base class for OSC stream framing strategies."""

    @abstractmethod
    def encode(self, dgram: bytes) -> bytes:
        """Encode a single OSC datagram for transmission on a byte stream.

        Args:
            dgram: Raw OSC datagram bytes.

        Returns:
            The framed byte sequence to write to the stream.
        """

    @abstractmethod
    def decode_stream(
        self, buf: bytes | bytearray, start: int = 0
    ) -> tuple[list[bytes], int]:
        """Decode complete OSC datagrams from a byte buffer.

        Args:
            buf: Bytes received from a stream.
            start: The index in ``buf`` to start decoding from.

        Returns:
            A tuple ``(messages, bytes consumed)``.
        """


class SLIPFraming(Framing):
    """SLIP (RFC 1055) framing for OSC 1.1.

    See the "OSC Delivery Specification 1.1" section from the 2009 NIME paper for details.
    """

    def encode(self, dgram: bytes) -> bytes:
        return slip_encode(dgram)

    def decode_stream(
        self, buf: bytes | bytearray, start: int = 0
    ) -> tuple[list[bytes], int]:
        pos = start
        messages = []

        scan = start
        while (end := buf.find(END, scan)) >= 0:
            if end > scan:
                messages.append(slip_decode(bytes(buf[scan:end])))
                pos = end + len(END)
            scan = end + len(END)

        # Consume trailing delimiters, but retain an incomplete packet.
        if scan == len(buf):
            pos = scan

        return messages, pos - start


class BinaryLengthFraming(Framing):
    """Length-prefixed framing for OSC 1.0.

    See the "OSC Packets" section from OSC 1.0 Specification for details.
    """

    def encode(self, dgram: bytes) -> bytes:
        if dgram:
            return pack("!I", len(dgram)) + dgram
        return b""

    def decode_stream(
        self, buf: bytes | bytearray, start: int = 0
    ) -> tuple[list[bytes], int]:
        messages = []
        pos = start

        while (data_pos := pos + 4) < len(buf):
            (length,) = unpack_from("!I", buf, pos)
            end = data_pos + length

            if end > len(buf):
                break

            messages.append(bytes(buf[data_pos:end]))

            pos = end

        return messages, pos - start


class FramingParser:
    """Stateful stream decoder for (framed) OSC byte stream.

    Not safe for concurrent use.

    Args:
        framing: Strategy used to decode buffered stream data.
        max_buffer_size: Maximum size of the internal buffer.
    """

    __slots__ = ("buf", "start", "framing", "max_buffer_size")

    def __init__(self, framing: Framing, max_buffer_size: int = 1048576) -> None:
        self.buf = bytearray()
        self.start = 0
        self.framing = framing
        self.max_buffer_size = max_buffer_size

    def feed(self, chunk: bytes | bytearray | memoryview) -> list[bytes]:
        """Append stream data to the internal buffer and return any complete OSC datagrams.

        Args:
            chunk: Newly received bytes from the stream.

        Returns:
            A list of complete, decoded OSC datagrams.
        """

        new_buf_len = len(self.buf) + len(chunk)

        if (pending := new_buf_len - self.start) > self.max_buffer_size:
            raise ValueError(f"Buffer is too large: {pending} > {self.max_buffer_size}")

        if new_buf_len > self.max_buffer_size:
            del self.buf[: self.start]
            self.start = 0

        self.buf.extend(chunk)

        messages, consumed = self.framing.decode_stream(self.buf, self.start)
        available = len(self.buf) - self.start

        assert 0 <= consumed <= available, (
            f"misbehaving framing decoder: {consumed=} {available=}"
        )

        self.start += consumed

        return messages

    @property
    def remaining(self) -> bytes:
        """Return any unparsed bytes."""

        return bytes(self.buf[self.start :])

    def reset(self) -> None:
        """Clear the internal buffer (discard unparsed data)."""

        del self.buf[:]
        self.start = 0


SLIP_FRAMING: Framing = SLIPFraming()
BINARY_LENGTH_FRAMING: Framing = BinaryLengthFraming()
