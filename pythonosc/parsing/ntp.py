"""Parsing and conversion of NTP dates contained in datagrams."""

import datetime
import struct
import time


JAN_1970 = 2208988800
SECS_TO_PICOS = 4294967296

# 63 zero bits followed by a one in the least signifigant bit is a special
# case meaning "immediately."
IMMEDIATELY = struct.pack('>q', 1)

# From NTP lib.
_SYSTEM_EPOCH = datetime.date(*time.gmtime(0)[0:3])
_NTP_EPOCH = datetime.date(1900, 1, 1)
_NTP_DELTA = (_SYSTEM_EPOCH - _NTP_EPOCH).days * 24 * 3600


class NtpError(Exception):
  """Base class for ntp module errors."""


def ntp_to_system_time(date):
    """Convert a NTP time to system time.

    System time is reprensented by seconds since the epoch in UTC.
    """
    return date - _NTP_DELTA

def system_time_to_ntp(date):
    """ since 1970 => since 1900 64b OSC """
    sec_1970 = int(date)
    sec_1900 = sec_1970 + JAN_1970
    
    sec_frac = float(date - sec_1970)
    picos = int(sec_frac * SECS_TO_PICOS)
    
    return struct.pack('>I', int(sec_1900)) + struct.pack('>I', picos)
