"""Functions to get OSC types from datagrams and vice versa"""

import decimal
import struct

from pythonosc.parsing import ntp


class ParseError(Exception):
  """Base exception for when a datagram parsing error occurs."""


class BuildError(Exception):
  """Base exception for when a datagram building error occurs."""


# Constant for special ntp datagram sequences that represent an immediate time.
IMMEDIATELY = 0

# Datagram length in bytes for types that have a fixed size.
_INT_DGRAM_LEN = 4
_FLOAT_DGRAM_LEN = 4
_DATE_DGRAM_LEN = _INT_DGRAM_LEN * 2
# Strings and blob dgram length is always a multiple of 4 bytes.
_STRING_DGRAM_PAD = 4
_BLOB_DGRAM_PAD = 4


def write_string(val):
  """Returns the OSC string equivalent of the given python string.

  Raises:
    - BuildError if the string could not be encoded.
  """
  try:
    dgram = val.encode('utf-8')  # Default, but better be explicit.
  except (UnicodeEncodeError, AttributeError) as e:
    raise BuildError('Incorrect string, could not encode {}'.format(e))
  diff = _STRING_DGRAM_PAD - (len(dgram) % _STRING_DGRAM_PAD)
  dgram += (b'\x00' * diff)
  return dgram


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
      raise ParseError(
          'OSC string cannot begin with a null byte: %s' % dgram[start_index:])
    # Align to a byte word.
    if (offset) % _STRING_DGRAM_PAD == 0:
      offset += _STRING_DGRAM_PAD
    else:
      offset += (-offset % _STRING_DGRAM_PAD)
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


def write_int(val):
  """Returns the datagram for the given integer parameter value

  Raises:
    - BuildError if the int could not be converted.
  """
  try:
    return struct.pack('>i', val)
  except struct.error as e:
    raise BuildError('Wrong argument value passed: {}'.format(e))


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
        struct.unpack('>i',
                      dgram[start_index:start_index + _INT_DGRAM_LEN])[0],
        start_index + _INT_DGRAM_LEN)
  except (struct.error, TypeError) as e:
    raise ParseError('Could not parse datagram %s' % e)


def write_float(val):
  """Returns the datagram for the given float parameter value

  Raises:
    - BuildError if the float could not be converted.
  """
  try:
    return struct.pack('>f', val)
  except struct.error as e:
    raise BuildError('Wrong argument value passed: {}'.format(e))


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
      # Noticed that Reaktor doesn't send the last bunch of \x00 needed to make
      # the float representation complete in some cases, thus we pad here to
      # account for that.
      dgram = dgram + b'\x00' * (_FLOAT_DGRAM_LEN - len(dgram[start_index:]))
    return (
        struct.unpack('>f',
                      dgram[start_index:start_index + _FLOAT_DGRAM_LEN])[0],
        start_index + _FLOAT_DGRAM_LEN)
  except (struct.error, TypeError) as e:
    raise ParseError('Could not parse datagram %s' % e)


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
  total_size = size + (-size % _BLOB_DGRAM_PAD)
  end_index = int_offset + size
  if end_index - start_index > len(dgram[start_index:]):
    raise ParseError('Datagram is too short.')
  return dgram[int_offset:int_offset + size], int_offset + total_size


def write_blob(val):
  """Returns the datagram for the given blob parameter value.

  Raises:
    - BuildError if the value was empty or if its size didn't fit an OSC int.
  """
  if not val:
    raise BuildError('Blob value cannot be empty')
  dgram = write_int(len(val))
  dgram += val
  while len(dgram) % _BLOB_DGRAM_PAD != 0:
    dgram += b'\x00'
  return dgram


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
    returns osc_immediately (0) if the corresponding OSC sequence was found.

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
  # Sum seconds and fraction of second:
  system_time = num_secs + (fraction / ntp.FRACTIONAL_CONVERSION)
  return ntp.ntp_to_system_time(system_time), start_index


def write_date(system_time):
  if system_time == IMMEDIATELY:
    return ntp.IMMEDIATELY

  try:
    return ntp.system_time_to_ntp(system_time)
  except ntp.NtpError as ntpe:
    raise BuildError(ntpe)


def write_rgba(val):
  """Returns the datagram for the given rgba32 parameter value

  Raises:
    - BuildError if the int could not be converted.
  """
  try:
    return struct.pack('>I', val)
  except struct.error as e:
    raise BuildError('Wrong argument value passed: {}'.format(e))


def get_rgba(dgram, start_index):
  """Get an rgba32 integer from the datagram.

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
        struct.unpack('>I',
                      dgram[start_index:start_index + _INT_DGRAM_LEN])[0],
        start_index + _INT_DGRAM_LEN)
  except (struct.error, TypeError) as e:
    raise ParseError('Could not parse datagram %s' % e)
