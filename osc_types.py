import struct


class ParseError(Exception):
  """Base exception for when a datagram parsing error occurs."""


def GetString(dgram, start_index):
  """Get an OSC string from the datagram, starting at pos start_index.

  A sequence of non-null ASCII characters followed by a null,
  followed by 0-3 additional null characters to make the total number
  of bits a multiple of 32.

  Args:
    dgram: a datagram packet
    start_index: an index where the string starts in the datagram

  Returns:
    A the sub datagram containing the string and the end index.

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
