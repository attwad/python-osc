"""Parsing and conversion of NTP dates contained in datagrams."""

import datetime
import struct
import time

# conversion factor for fractional seconds (maximum value of fractional part)
FRACTIONAL_CONVERSION = 2 ** 32

# 63 zero bits followed by a one in the least signifigant bit is a special
# case meaning "immediately."
IMMEDIATELY = struct.pack('>q', 1)

# From NTP lib.
_SYSTEM_EPOCH = datetime.date(*time.gmtime(0)[0:3])
_NTP_EPOCH = datetime.date(1900, 1, 1)
# _NTP_DELTA is 2208988800
_NTP_DELTA = (_SYSTEM_EPOCH - _NTP_EPOCH).days * 24 * 3600


class NtpError(Exception):
  """Base class for ntp module errors."""


def ntp_to_system_time(date):
    """Convert a NTP time to system time.

    System time is reprensented by seconds since the epoch in UTC.
    """
    return date - _NTP_DELTA

def system_time_to_ntp(date):
    """Convert a system time to NTP time.

    System time is reprensented by seconds since the epoch in UTC.
    """
    try:
      num_secs = int(date)
    except ValueError as e:
      raise NtpError(e)
    
    num_secs_ntp = num_secs + _NTP_DELTA
    
    sec_frac = float(date - num_secs)

    picos = int(sec_frac * FRACTIONAL_CONVERSION)
  
    return struct.pack('>I', int(num_secs_ntp)) + struct.pack('>I', picos)
