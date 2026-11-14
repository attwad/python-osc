from pytest import fixture, mark, raises

from pythonosc.parsing.framing import (
    BinaryLengthFraming,
    Framing,
    FramingParser,
    SLIPFraming,
)


class SquareFraming(Framing):
    """Framing strategy for ease of testing, wraps everything in [] brackets."""

    def encode(self, data: bytes) -> bytes:
        if data:
            return b"[" + data + b"]"
        return b""

    def decode_stream(
        self, chunk: bytes | bytearray, start: int = 0
    ) -> tuple[list[bytes], int]:
        out = []
        pos = start

        while (a := chunk.find(b"[", pos)) >= 0:
            a += 1

            if (b := chunk.find(b"]", a)) >= 0:
                out.append(bytes(chunk[a:b]))
                pos = b + 1
            else:
                break

        return out, pos - start


class CommonFramingTest:
    def test_encode_decode(self, framing: Framing) -> None:
        messages = [b"test1", b"", b"test2", b"test3"]
        expected = [m for m in messages if m]
        data = b"".join(framing.encode(message) for message in messages)

        assert framing.decode_stream(data) == (expected, len(data))

    @mark.parametrize("n,m", [(1, 1), (4, 1), (64, 0)])
    def test_incomplete(self, framing: Framing, n: int, m: int) -> None:
        message_a = framing.encode(b"test")
        message_b = framing.encode(b"cut here")
        data = (message_a + message_b)[:-n]
        messages, consumed = framing.decode_stream(data)

        assert messages == messages[:m]
        assert data[consumed:] == data[len(message_a) :]

    def test_decode_with_start(self, framing: Framing) -> None:
        garbage = b"garbage"
        data = garbage + framing.encode(b"test")

        assert framing.decode_stream(data, len(garbage)) == (
            [b"test"],
            len(data) - len(garbage),
        )


class TestSLIPFraming(CommonFramingTest):
    @fixture
    def framing(self) -> Framing:
        return SLIPFraming()

    def test_encode(self, framing: Framing) -> None:
        assert framing.encode(b"te\xc0st") == b"\xc0te\xdb\xdcst\xc0"

    @mark.parametrize("prefix", [b"", b"\xc0"])
    def test_single_end_separates_packets(
        self, framing: Framing, prefix: bytes
    ) -> None:
        data = prefix + b"one\xc0two\xc0"
        assert framing.decode_stream(data) == ([b"one", b"two"], len(data))

    @mark.parametrize("count", [1, 2, 3, 5])
    def test_end_markers_do_not_emit_empty_packets(
        self, framing: Framing, count: int
    ) -> None:
        data = b"\xc0" * count
        assert framing.decode_stream(data) == ([], len(data))

    @mark.parametrize("leading_end", [False, True])
    def test_every_stream_split_preserves_packets(
        self, framing: Framing, leading_end: bool
    ) -> None:
        expected = [b"one", b"two\xc0\xdb", b"three"]
        data = b"".join(framing.encode(value)[not leading_end :] for value in expected)
        for split in range(len(data) + 1):
            parser = FramingParser(framing)
            actual = parser.feed(data[:split]) + parser.feed(data[split:])
            assert actual == expected, split
            assert parser.remaining == b""

    def test_bytewise_stream_preserves_packets(self, framing: Framing) -> None:
        parser = FramingParser(framing)
        expected = [b"one", b"two\xc0\xdb"]
        data = b"".join(framing.encode(value) for value in expected)
        actual = []
        for byte in data:
            actual.extend(parser.feed(bytes([byte])))
        assert actual == expected
        assert parser.remaining == b""


class TestBinaryLengthFraming(CommonFramingTest):
    @fixture
    def framing(self) -> Framing:
        return BinaryLengthFraming()

    def test_encode(self, framing: Framing) -> None:
        assert framing.encode(b"test") == b"\x00\x00\x00\x04test"


class TestSquareFraming(CommonFramingTest):
    @fixture
    def framing(self) -> Framing:
        return SquareFraming()

    def test_encode(self, framing: Framing) -> None:
        assert framing.encode(b"test") == b"[test]"


class TestFramingParser:
    @fixture
    def parser(self) -> FramingParser:
        return FramingParser(SquareFraming(), max_buffer_size=16)

    def test_cold(self, parser: FramingParser) -> None:
        assert parser.feed(b"[test]") == [b"test"]

    def test_hot(self, parser: FramingParser) -> None:
        assert parser.feed(b"[test") == []
        assert parser.feed(b"123][xxx]") == [b"test123", b"xxx"]

    def test_large_buffer(self, parser: FramingParser) -> None:
        parser.feed(b"[test]")

        with raises(ValueError, match="Buffer is too large: 18 > 16"):
            parser.feed(b"[test]" * 3)

    def test_compaction(self, parser: FramingParser) -> None:
        for _ in range(4):
            assert parser.feed(b"[tests]") == [b"tests"]

    def test_reset(self, parser: FramingParser) -> None:
        parser.feed(b"[test]")
        parser.feed(b"[xxx")

        assert parser.remaining == b"[xxx"

        parser.reset()

        assert parser.remaining == b""
