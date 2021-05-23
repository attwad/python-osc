import unittest
import time

from pythonosc.parsing import ntp


class TestNTP(unittest.TestCase):
    """ TODO: Write real tests for this when I get time..."""

    def test_nto_to_system_time(self):
        unix_time = time.time()
        timestamp = ntp.system_time_to_ntp(unix_time)
        unix_time2 = ntp.ntp_to_system_time(timestamp)
        self.assertTrue(type(unix_time) is float)
        self.assertTrue(type(timestamp) is bytes)
        self.assertTrue(type(unix_time2) is float)
        self.assertAlmostEqual(unix_time, unix_time2, places=5)


if __name__ == "__main__":
    unittest.main()
