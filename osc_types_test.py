import unittest

import osc_types


class TestOscMessage(unittest.TestCase):

  def test_get_string(self):
    cases = {
      b"A\x00\x00\x00": (b"A\x00\x00\x00", 4),
      b"AB\x00\x00": (b"AB\x00\x00", 4),
      b"ABC\x00": (b"ABC\x00", 4),
      b"ABCD\x00\x00\x00\x00": (b"ABCD\x00\x00\x00\x00", 8),

      b"ABCD\x00\x00\x00\x00GARBAGE": (b"ABCD\x00\x00\x00\x00", 8),
    }

    for dgram, expected in cases.items():
      self.assertEquals(expected, osc_types.GetString(dgram, 0))

  def test_get_string_raises_on_wrong_dgram(self):
    cases = [
      b"\x00\x00\x00\x00",
      b'blablaba',
      b'',
      b'\x00',
    ]

    for case in cases:
      self.assertRaises(osc_types.ParseError, osc_types.GetString, case, 0)

  def test_get_string_raises_on_wrong_start_index(self):
    self.assertRaises(osc_types.ParseError, osc_types.GetString, b'abc\x00', 1)

  def test_get_string_raises_on_wrong_start_index_negative(self):
    self.assertRaises(osc_types.ParseError, osc_types.GetString, b'abc\x00', -1)

if __name__ == "__main__":
  unittest.main()
