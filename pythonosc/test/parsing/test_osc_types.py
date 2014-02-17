"""Unit tests for the osc_types module."""
import unittest

from pythonosc.parsing import ntp
from pythonosc.parsing import osc_types


class TestString(unittest.TestCase):

  def test_get_string(self):
    cases = {
        b"A\x00\x00\x00": ("A", 4),
        b"AB\x00\x00": ("AB", 4),
        b"ABC\x00": ("ABC", 4),
        b"ABCD\x00\x00\x00\x00": ("ABCD", 8),

        b"ABCD\x00\x00\x00\x00GARBAGE": ("ABCD", 8),
    }

    for dgram, expected in cases.items():
      self.assertEqual(expected, osc_types.get_string(dgram, 0))

  def test_get_string_raises_on_wrong_dgram(self):
    cases = [
        b"\x00\x00\x00\x00",
        b'blablaba',
        b'',
        b'\x00',
        True,
    ]

    for case in cases:
        self.assertRaises(
            osc_types.ParseError, osc_types.get_string, case, 0)

  def test_get_string_raises_when_datagram_too_short(self):
    self.assertRaises(
        osc_types.ParseError, osc_types.get_string, b'abc\x00', 1)

  def test_get_string_raises_on_wrong_start_index_negative(self):
    self.assertRaises(
        osc_types.ParseError, osc_types.get_string, b'abc\x00', -1)


class TestInteger(unittest.TestCase):

  def test_get_integer(self):
    cases = {
        b"\x00\x00\x00\x00": (0, 4),
        b"\x00\x00\x00\x01": (1, 4),
        b"\x00\x00\x00\x02": (2, 4),
        b"\x00\x00\x00\x03": (3, 4),

        b"\x00\x00\x01\x00": (256, 4),
        b"\x00\x01\x00\x00": (65536, 4),
        b"\x01\x00\x00\x00": (16777216, 4),

        b"\x00\x00\x00\x01GARBAGE": (1, 4),
    }

    for dgram, expected in cases.items():
        self.assertEqual(
            expected, osc_types.get_int(dgram, 0))

  def test_get_integer_raises_on_type_error(self):
    cases = [b'', True]

    for case in cases:
      self.assertRaises(osc_types.ParseError, osc_types.get_int, case, 0)

  def test_get_integer_raises_on_wrong_start_index(self):
    self.assertRaises(
        osc_types.ParseError, osc_types.get_int, b'\x00\x00\x00\x11', 1)

  def test_get_integer_raises_on_wrong_start_index_negative(self):
    self.assertRaises(
        osc_types.ParseError, osc_types.get_int, b'\x00\x00\x00\x00', -1)

  def test_datagram_too_short(self):
    dgram = b'\x00' * 3
    self.assertRaises(osc_types.ParseError, osc_types.get_int, dgram, 2)


class TestFloat(unittest.TestCase):

  def test_get_float(self):
    cases = {
        b"\x00\x00\x00\x00": (0.0, 4),
        b"?\x80\x00\x00'": (1.0, 4),
        b'@\x00\x00\x00': (2.0, 4),

        b"\x00\x00\x00\x00GARBAGE": (0.0, 4),
    }

    for dgram, expected in cases.items():
      self.assertAlmostEqual(expected, osc_types.get_float(dgram, 0))

  def test_get_float_raises_on_wrong_dgram(self):
    cases = [True]

    for case in cases:
      self.assertRaises(osc_types.ParseError, osc_types.get_float, case, 0)

  def test_get_float_raises_on_type_error(self):
    cases = [None]

    for case in cases:
      self.assertRaises(osc_types.ParseError, osc_types.get_float, case, 0)

  def test_datagram_too_short_pads(self):
    dgram = b'\x00' * 2
    self.assertEqual((0, 4), osc_types.get_float(dgram, 0))


class TestBlob(unittest.TestCase):

  def test_get_blob(self):
    cases = {
        b"\x00\x00\x00\x00": (b"", 4),
        b"\x00\x00\x00\x08stuff\x00\x00\x00": (b"stuff\x00\x00\x00", 12),
        b"\x00\x00\x00\x04\x00\x00\x00\x00": (b"\x00\x00\x00\x00", 8),
        b"\x00\x00\x00\x02\x00\x00\x00\x00": (b"\x00\x00", 8),

        b"\x00\x00\x00\x08stuff\x00\x00\x00datagramcontinues": (
            b"stuff\x00\x00\x00", 12),
    }

    for dgram, expected in cases.items():
      self.assertEqual(expected, osc_types.get_blob(dgram, 0))

  def test_get_blob_raises_on_wrong_dgram(self):
    cases = [b'', True, b"\x00\x00\x00\x08"]

    for case in cases:
      self.assertRaises(osc_types.ParseError, osc_types.get_blob, case, 0)

  def test_get_blob_raises_on_wrong_start_index(self):
    self.assertRaises(
        osc_types.ParseError, osc_types.get_blob, b'\x00\x00\x00\x11', 1)

  def test_get_blob_raises_too_short_buffer(self):
    self.assertRaises(
        osc_types.ParseError,
        osc_types.get_blob,
        b'\x00\x00\x00\x11\x00\x00', 1)

  def test_get_blog_raises_on_wrong_start_index_negative(self):
    self.assertRaises(
        osc_types.ParseError, osc_types.get_blob, b'\x00\x00\x00\x00', -1)


class TestNTPTimestamp(unittest.TestCase):

  def test_immediately_dgram(self):
    dgram = ntp.IMMEDIATELY
    self.assertEqual(osc_types.IMMEDIATELY, osc_types.get_date(dgram, 0)[0])

  def test_origin_of_time(self):
    dgram = b'\x00' * 8
    self.assertGreater(0, osc_types.get_date(dgram, 0)[0])

  def test_datagram_too_short(self):
    dgram = b'\x00' * 8
    self.assertRaises(osc_types.ParseError, osc_types.get_date, dgram, 2)

  def test_write_date(self):
    self.assertEqual(b'\x83\xaa~\x83\x00\x00\x059', osc_types.write_date(3.1337))


class TestBuildMethods(unittest.TestCase):

  def test_string(self):
    self.assertEqual(b'\x00\x00\x00\x00', osc_types.write_string(''))
    self.assertEqual(b'A\x00\x00\x00', osc_types.write_string('A'))
    self.assertEqual(b'AB\x00\x00', osc_types.write_string('AB'))
    self.assertEqual(b'ABC\x00', osc_types.write_string('ABC'))
    self.assertEqual(b'ABCD\x00\x00\x00\x00', osc_types.write_string('ABCD'))

  def test_string_raises(self):
    self.assertRaises(osc_types.BuildError, osc_types.write_string, 123)

  def test_int(self):
    self.assertEqual(b'\x00\x00\x00\x00', osc_types.write_int(0))
    self.assertEqual(b'\x00\x00\x00\x01', osc_types.write_int(1))

  def test_int_raises(self):
    self.assertRaises(osc_types.BuildError, osc_types.write_int, 'no int')

  def test_float(self):
    self.assertEqual(b'\x00\x00\x00\x00', osc_types.write_float(0.0))
    self.assertEqual(b'?\x00\x00\x00', osc_types.write_float(0.5))
    self.assertEqual(b'?\x80\x00\x00', osc_types.write_float(1.0))
    self.assertEqual(b'?\x80\x00\x00', osc_types.write_float(1))

  def test_float_raises(self):
    self.assertRaises(osc_types.BuildError, osc_types.write_float, 'no float')

  def test_blob(self):
    self.assertEqual(
        b'\x00\x00\x00\x02\x00\x01\x00\x00',
        osc_types.write_blob(b'\x00\x01'))
    self.assertEqual(
        b'\x00\x00\x00\x04\x00\x01\x02\x03',
        osc_types.write_blob(b'\x00\x01\x02\x03'))

  def test_blob_raises(self):
    self.assertRaises(osc_types.BuildError, osc_types.write_blob, b'')


if __name__ == "__main__":
  unittest.main()
