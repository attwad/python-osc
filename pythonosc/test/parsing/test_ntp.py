import unittest

from pythonosc.parsing import ntp


class TestNTP(unittest.TestCase):
  """ TODO: Write real tests for this when I get time..."""

  def test_nto_to_system_time(self):
    self.assertGreater(0, ntp.ntp_to_system_time(0))

  def test_system_time_to_ntp(self):
    self.assertTrue(ntp.system_time_to_ntp(0.0))


if __name__ == "__main__":
  unittest.main()
