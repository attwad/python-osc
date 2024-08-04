#  This file is part of the SlipLib project which is released under the MIT license.
#  See https://github.com/rhjdjong/SlipLib for details.
#
# The MIT License (MIT)
#
# Copyright (c) 2015 Ruud de Jong
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import re

END = b"\xc0"
ESC = b"\xdb"
ESC_END = b"\xdc"
ESC_ESC = b"\xdd"
END_END = b"\xc0\xc0"
"""These constants represent the special SLIP bytes"""


class ProtocolError(ValueError):
    """Exception to indicate that a SLIP protocol error has occurred.

    This exception is raised when an attempt is made to decode
    a packet with an invalid byte sequence.
    An invalid byte sequence is either an :const:`ESC` byte followed
    by any byte that is not an :const:`ESC_ESC` or :const:`ESC_END` byte,
    or a trailing :const:`ESC` byte as last byte of the packet.

    The :exc:`ProtocolError` carries the invalid packet
    as the first (and only) element in in its :attr:`args` tuple.
    """


def encode(msg: bytes) -> bytes:
    """Encodes a message (a byte sequence) into a SLIP-encoded packet.

    Args:
        msg: The message that must be encoded

    Returns:
        The SLIP-encoded message
    """
    if msg:
        msg = bytes(msg)
    else:
        msg = b""
    return END + msg.replace(ESC, ESC + ESC_ESC).replace(END, ESC + ESC_END) + END


def decode(packet: bytes) -> bytes:
    """Retrieves the message from the SLIP-encoded packet.

    Args:
        packet: The SLIP-encoded message.
           Note that this must be exactly one complete packet.
           The :func:`decode` function does not provide any buffering
           for incomplete packages, nor does it provide support
           for decoding data with multiple packets.
    Returns:
        The decoded message

    Raises:
        ProtocolError: if the packet contains an invalid byte sequence.
    """
    if not is_valid(packet):
        raise ProtocolError(packet)
    return packet.strip(END).replace(ESC + ESC_END, END).replace(ESC + ESC_ESC, ESC)


def is_valid(packet: bytes) -> bool:
    """Indicates if the packet's contents conform to the SLIP specification.

    A packet is valid if:

    * It contains no :const:`END` bytes other than leading and/or trailing :const:`END` bytes, and
    * Each :const:`ESC` byte is followed by either an :const:`ESC_END` or an :const:`ESC_ESC` byte.

    Args:
        packet: The packet to inspect.

    Returns:
        :const:`True` if the packet is valid, :const:`False` otherwise
    """
    packet = packet.strip(END)
    return not (
        END in packet
        or packet.endswith(ESC)
        or re.search(ESC + b"[^" + ESC_END + ESC_ESC + b"]", packet)
    )
