"""Module containing parsing functions to get OSC types from datagrams."""

import decimal
import struct
import time

from parsing import ntp


class ParseError(Exception):
  """Base exception for when a datagram parsing error occurs."""


# Constant for special ntp datagram sequences that represent an immediate time.
IMMEDIATELY = "IMMEDIATELY"

# Datagram length for types that have a fixed size.
_INT_DGRAM_LEN = 4
_FLOAT_DGRAM_LEN = 4
_DATE_DGRAM_LEN = _INT_DGRAM_LEN * 2


def get_string(dgram, start_index):
  """Get a python string from the datagram, starting at pos start_index.

  According to the specifications, a string is:
  "A sequence of non-null ASCII characters followed by a null,
  followed by 0-3 additional null characters to make the total number
  of bits a multiple of 32".

  Args:
    dgram: A datagram packet.
    start_index: An index where the string starts in the datagram.

  Returns:
    A tuple containing the string and the new end index.

  Raises:
    ParseError if the datagram could not be parsed.
  """
  offset = 0
  try:
    while dgram[start_index + offset] != 0:
      offset += 1
    if offset == 0:
      raise ParseError('OSC string cannot begin with a null byte')
    # Align to a byte word.
    if (offset) % 4 == 0:
      offset += 4
    else:
      offset += (-offset % 4)
    # Python slices do not raise an IndexError past the last index,
    # do it ourselves.
    if offset > len(dgram[start_index:]):
      raise ParseError('Datagram is too short')
    data_str = dgram[start_index:start_index + offset]
    return data_str.replace(b'\x00', b'').decode('utf-8'), start_index + offset
  except IndexError as ie:
    raise ParseError('Could not parse datagram %s' % ie)
  except TypeError as te:
    raise ParseError('Could not parse datagram %s' % te)


def get_int(dgram, start_index):
  """Get a 32-bit big-endian two's complement integer from the datagram.

  Args:
    dgram: A datagram packet.
    start_index: An index where the integer starts in the datagram.

  Returns:
    A tuple containing the integer and the new end index.

  Raises:
    ParseError if the datagram could not be parsed.
  """
  try:
    if len(dgram[start_index:]) < _INT_DGRAM_LEN:
      raise ParseError('Datagram is too short')
    return (
        struct.unpack('>i', dgram[start_index:start_index+_INT_DGRAM_LEN])[0],
        start_index + _INT_DGRAM_LEN)
  except struct.error as se:
    raise ParseError('Cannot parse integer: %s' % se)
  except TypeError as te:
    raise ParseError('Could not parse datagram %s' % te)


def get_float(dgram, start_index):
  """Get a 32-bit big-endian IEEE 754 floating point number from the datagram.

  Args:
    dgram: A datagram packet.
    start_index: An index where the float starts in the datagram.

  Returns:
    A tuple containing the float and the new end index.

  Raises:
    ParseError if the datagram could not be parsed.
  """
  try:
    if len(dgram[start_index:]) < _FLOAT_DGRAM_LEN:
      raise ParseError('Datagram is too short')
    return (
        struct.unpack('>f', dgram[start_index:start_index+_FLOAT_DGRAM_LEN])[0],
        start_index + _FLOAT_DGRAM_LEN)
  except struct.error as se:
    raise ParseError('Cannot parse float: %s' % se)
  except TypeError as te:
    raise ParseError('Could not parse datagram %s' % te)


def get_blob(dgram, start_index):
  """ Get a blob from the datagram.
  
  According to the specifications, a blob is made of
  "an int32 size count, followed by that many 8-bit bytes of arbitrary
  binary data, followed by 0-3 additional zero bytes to make the total
  number of bits a multiple of 32".

  Args:
    dgram: A datagram packet.
    start_index: An index where the float starts in the datagram.

  Returns:
    A tuple containing the blob and the new end index.

  Raises:
    ParseError if the datagram could not be parsed.
  """
  size, int_offset = get_int(dgram, start_index)
  # Make the size a multiple of 32 bits.
  size += (-size % 4)
  end_index = int_offset + size
  if end_index - start_index > len(dgram[start_index:]):
    raise ParseError('Datagram is too short.')
  try:
    return dgram[int_offset:end_index], end_index
  except TypeError as te:
    raise ParseError('Could not parse datagram %s' % te)


def get_date(dgram, start_index):
  """Get a 64-bit big-endian fixed-point time tag as a date from the datagram.

  According to the specifications, a date is represented as is:
  "the first 32 bits specify the number of seconds since midnight on
  January 1, 1900, and the last 32 bits specify fractional parts of a second
  to a precision of about 200 picoseconds".

  Args:
    dgram: A datagram packet.
    start_index: An index where the date starts in the datagram.

  Returns:
    A tuple containing the system date and the new end index.

  Raises:
    ParseError if the datagram could not be parsed.
  """
  # Check for the special case first.
  if dgram[start_index:start_index + _DATE_DGRAM_LEN] == ntp.IMMEDIATELY:
    return IMMEDIATELY, start_index + _DATE_DGRAM_LEN
  if len(dgram[start_index:]) < _DATE_DGRAM_LEN:
    raise ParseError('Datagram is too short')
  num_secs, start_index = get_int(dgram, start_index)
  fraction, start_index = get_int(dgram, start_index)
  # Get a decimal representation from those two values.
  dec = decimal.Decimal(str(num_secs) + '.' + str(fraction))
  # And convert it to float simply.
  system_time = float(dec)
  return ntp.ntp_to_system_time(system_time), start_index
