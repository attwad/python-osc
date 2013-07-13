"""Module containing parsing functions to get OSC types from datagrams."""
import decimal
import ntp
import struct
import time


class ParseError(Exception):
  """Base exception for when a datagram parsing error occurs."""


# Constant for special ntp datagram sequences that represent an immediate time.
IMMEDIATELY = "IMMEDIATELY"

# Datagram length for types that have a fixed size.
_INT_DGRAM_LEN = 4
_FLOAT_DGRAM_LEN = 4
_DATE_DGRAM_LEN = _INT_DGRAM_LEN * 2


def GetString(dgram, start_index):
  """Get an OSC string from the datagram, starting at pos start_index.

  According to the specifications, a string is:
  "A sequence of non-null ASCII characters followed by a null,
  followed by 0-3 additional null characters to make the total number
  of bits a multiple of 32".

  Args:
    dgram: A datagram packet.
    start_index: An index where the string starts in the datagram.

  Returns:
    A tuple containing the string and the end index.

  Raises:
    ParseError if the datagram could not be parsed.
  """
  current_index = start_index
  try:
    while dgram[current_index] != 0:
      current_index += 1
    if current_index == start_index:
      raise ParseError('OSC string cannot begin with a null byte')
    # Align to a byte word.
    if current_index % 4 == 0:
      current_index += 4
    else:
      current_index += (-current_index % 4)
    # Python slices do not raise an IndexError past the last index.
    if start_index + current_index > len(dgram[start_index:]):
      raise ParseError('OSC String is too short')
    return dgram[start_index:start_index+current_index], current_index
  except IndexError as ie:
    raise ParseError('Could not parse datagram %s' % ie)
  except TypeError as te:
    raise ParseError('Could not parse datagram %s' % te)


def GetInteger(dgram, start_index):
  """Get a 32-bit big-endian two's complement integer from the datagram.

  Args:
    dgram: A datagram packet.
    start_index: An index where the integer starts in the datagram.

  Returns:
    A tuple containing the integer and the end index.

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


def GetFloat(dgram, start_index):
  """Get a 32-bit big-endian IEEE 754 floating point number from the datagram.

  Args:
    dgram: A datagram packet.
    start_index: An index where the float starts in the datagram.

  Returns:
    A tuple containing the float and the end index.

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


def GetBlob(dgram, start_index):
  """ Get a blob from the datagram.
  
  According to the specifications, a blob is made of
  "an int32 size count, followed by that many 8-bit bytes of arbitrary
  binary data, followed by 0-3 additional zero bytes to make the total
  number of bits a multiple of 32".

  Args:
    dgram: A datagram packet.
    start_index: An index where the float starts in the datagram.

  Returns:
    A tuple containing the blob and the end index.

  Raises:
    ParseError if the datagram could not be parsed.
  """
  size, int_offset = GetInteger(dgram, start_index)
  size += (-size % 4)
  end_index = start_index + int_offset + size
  if start_index + end_index > len(dgram):
    raise ParseError('Datagram is too short.')
  try:
    return dgram[start_index + int_offset:end_index], end_index
  except TypeError as te:
    raise ParseError('Could not parse datagram %s' % te)


def GetDate(dgram, start_index):
  """Get a 64-bit big-endian fixed-point time tag as a date from the datagram.

  According to the specifications, a date is represented as is:
  "the first 32 bits specify the number of seconds since midnight on
  January 1, 1900, and the last 32 bits specify fractional parts of a second
  to a precision of about 200 picoseconds".

  Args:
    dgram: A datagram packet.
    start_index: An index where the date starts in the datagram.

  Returns:
    A tuple containing the system date and the end index.

  Raises:
    ParseError if the datagram could not be parsed.
  """
  # Check for the special case first.
  if dgram == ntp.IMMEDIATELY:
    return IMMEDIATELY
  if len(dgram[start_index:]) < _DATE_DGRAM_LEN:
    raise ParseError('Datagram is too short')
  num_secs, start_index = GetInteger(dgram, start_index)
  fraction, start_index = GetInteger(dgram, start_index)
  # Get a decimal representation from those two values.
  dec = decimal.Decimal(str(num_secs) + '.' + str(fraction))
  # And convert it to float simply.
  system_time = float(dec)
  return ntp.NtpToSystemTime(system_time)
