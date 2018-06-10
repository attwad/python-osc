"""Unit tests for the osc_types module."""
import unittest

from pythonosc.parsing import ntp
from pythonosc.parsing import osc_types

from datetime import datetime


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


class TestRGBA(unittest.TestCase):

  def test_get_rgba(self):
    cases = {
        b"\x00\x00\x00\x00": (0, 4),
        b"\x00\x00\x00\x01": (1, 4),
        b"\x00\x00\x00\x02": (2, 4),
        b"\x00\x00\x00\x03": (3, 4),

        b"\xFF\x00\x00\x00": (4278190080, 4),
        b"\x00\xFF\x00\x00": (16711680, 4),
        b"\x00\x00\xFF\x00": (65280, 4),
        b"\x00\x00\x00\xFF": (255, 4),

        b"\x00\x00\x00\x01GARBAGE": (1, 4),
    }

    for dgram, expected in cases.items():
        self.assertEqual(
            expected, osc_types.get_rgba(dgram, 0))

  def test_get_rgba_raises_on_type_error(self):
    cases = [b'', True]

    for case in cases:
      self.assertRaises(osc_types.ParseError, osc_types.get_rgba, case, 0)

  def test_get_rgba_raises_on_wrong_start_index(self):
    self.assertRaises(
        osc_types.ParseError, osc_types.get_rgba, b'\x00\x00\x00\x11', 1)

  def test_get_rgba_raises_on_wrong_start_index_negative(self):
    self.assertRaises(
        osc_types.ParseError, osc_types.get_rgba, b'\x00\x00\x00\x00', -1)

  def test_datagram_too_short(self):
    dgram = b'\x00' * 3
    self.assertRaises(osc_types.ParseError, osc_types.get_rgba, dgram, 2)


class TestMidi(unittest.TestCase):

  def test_get_midi(self):
    cases = {
        b"\x00\x00\x00\x00": ((0,0,0,0), 4),
        b"\x00\x00\x00\x02": ((0,0,0,1), 4),
        b"\x00\x00\x00\x02": ((0,0,0,2), 4),
        b"\x00\x00\x00\x03": ((0,0,0,3), 4),

        b"\x00\x00\x01\x00": ((0,0,1,0), 4),
        b"\x00\x01\x00\x00": ((0,1,0,0), 4),
        b"\x01\x00\x00\x00": ((1,0,0,0), 4),

        b"\x00\x00\x00\x01GARBAGE": ((0,0,0,1), 4),
    }

    for dgram, expected in cases.items():
        self.assertEqual(
            expected, osc_types.get_midi(dgram, 0))

  def test_get_midi_raises_on_type_error(self):
    cases = [b'', True]

    for case in cases:
      self.assertRaises(osc_types.ParseError, osc_types.get_midi, case, 0)

  def test_get_midi_raises_on_wrong_start_index(self):
    self.assertRaises(
        osc_types.ParseError, osc_types.get_midi, b'\x00\x00\x00\x11', 1)

  def test_get_midi_raises_on_wrong_start_index_negative(self):
    self.assertRaises(
        osc_types.ParseError, osc_types.get_midi, b'\x00\x00\x00\x00', -1)

  def test_datagram_too_short(self):
    dgram = b'\x00' * 3
    self.assertRaises(osc_types.ParseError, osc_types.get_midi, dgram, 2)


class TestDate(unittest.TestCase):
    def test_get_ttag(self):
        cases = {
            b"\xde\x9c\x91\xbf\x00\x01\x00\x00": ((datetime(2018, 5, 8, 21, 14, 39), 65536), 8),
            b"\x00\x00\x00\x00\x00\x00\x00\x00": ((datetime(1900, 1, 1, 0, 0, 0), 0), 8),
            b"\x83\xaa\x7E\x80\x0A\x00\xB0\x0C": ((datetime(1970, 1, 1, 0, 0, 0), 167817228), 8)
        }

        for dgram, expected in cases.items():
            self.assertEqual(expected, osc_types.get_ttag(dgram, 0))

    def test_get_ttag_raises_on_wrong_start_index_negative(self):
        self.assertRaises(
            osc_types.ParseError, osc_types.get_ttag, b'\x00\x00\x00\x00\x00\x00\x00\x00', -1)

    def test_get_ttag_raises_on_type_error(self):
        cases = [b'', True]

        for case in cases:
            self.assertRaises(osc_types.ParseError, osc_types.get_ttag, case, 0)

    def test_get_ttag_raises_on_wrong_start_index(self):
        self.assertRaises(
            osc_types.ParseError, osc_types.get_date, b'\x00\x00\x00\x11\x00\x00\x00\x11', 1)

    def test_ttag_datagram_too_short(self):
        dgram = b'\x00' * 7
        self.assertRaises(osc_types.ParseError, osc_types.get_ttag, dgram, 6)

        dgram = b'\x00' * 2
        self.assertRaises(osc_types.ParseError, osc_types.get_ttag, dgram, 1)

        dgram = b'\x00' * 5
        self.assertRaises(osc_types.ParseError, osc_types.get_ttag, dgram, 4)

        dgram = b'\x00' * 1
        self.assertRaises(osc_types.ParseError, osc_types.get_ttag, dgram, 0)


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


class TestDouble(unittest.TestCase):

  def test_get_double(self):
    cases = {
        b'\x00\x00\x00\x00\x00\x00\x00\x00': (0.0, 8),
        b'?\xf0\x00\x00\x00\x00\x00\x00': (1.0, 8),
        b'@\x00\x00\x00\x00\x00\x00\x00': (2.0, 8),
        b'\xbf\xf0\x00\x00\x00\x00\x00\x00': (-1.0, 8),
        b'\xc0\x00\x00\x00\x00\x00\x00\x00': (-2.0, 8),

        b"\x00\x00\x00\x00\x00\x00\x00\x00GARBAGE": (0.0, 8),
    }

    for dgram, expected in cases.items():
      self.assertAlmostEqual(expected, osc_types.get_double(dgram, 0))

  def test_get_double_raises_on_wrong_dgram(self):
    cases = [True]

    for case in cases:
      self.assertRaises(osc_types.ParseError, osc_types.get_double, case, 0)

  def test_get_double_raises_on_type_error(self):
    cases = [None]

    for case in cases:
      self.assertRaises(osc_types.ParseError, osc_types.get_double, case, 0)

  def test_datagram_too_short_pads(self):
    dgram = b'\x00' * 2
    self.assertRaises(osc_types.ParseError, osc_types.get_double, dgram, 0)


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
    self.assertEqual(b'\x83\xaa~\x83\":)\xc7', osc_types.write_date(3.1337))


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
