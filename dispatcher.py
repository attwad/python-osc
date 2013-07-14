"""Class that maps OSC addresses to handlers."""
import re

class Dispatcher(object):
  """Register addresses to handlers and can match vice-versa."""

  def __init__(self):
    self._map = {}

  def map(self, address, handler):
    """Map a given address to a handler.

    Args:
      - address: An explicit endpoint.
      - handler: A function that will be run when the address matches with
                 the OscMessage passed as parameter.
    """
    # TODO: Check if we need to use a multimap instead, spec is a bit fuzzy
    # about it...
    self._map[address] = handler

  def handlers_for_address(self, address_pattern):
    """Return a tuple of handler matching the given OSC address pattern."""
    handlers = []
    # First convert the address_pattern into a matchable regexp.
    # '?' in the OSC Address Pattern matches any single character.
    # Let's consider numbers and _ "characters" too here, it's not said
    # explicitly in the specification but it sounds good.
    pattern = address_pattern.replace('?', '\\w?')
    # '*' in the OSC Address Pattern matches any sequence of zero or more
    # characters.
    pattern = pattern.replace('*', '\\w*')
    # The rest of the syntax in the specification is like the re module so
    # we're fine.
    pattern = pattern + '$'
    pattern = re.compile(pattern)
    matched = [handler for address, handler in self._map.items() if pattern.match(address)]
    return matched
