import unittest

import ntp


class TestNTP(unittest.TestCase):
  """ TODO: Write real tests for this when I get time..."""

  def testNtpToSystemTime(self):
    self.assertGreater(0, ntp.NtpToSystemTime(0))

  def testSystemToNtpTime(self):
    self.assertTrue(ntp.SystemToNtpTime(0.0))


if __name__ == "__main__":
  unittest.main()
