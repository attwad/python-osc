from typing import Union

from pythonosc.osc_bundle import OscBundle
from pythonosc.osc_message import OscMessage

import serial  # type: ignore


class SLIPClient:
    END = b'\xc0'
    ESC = b'\xdb'
    ESC_END = b'\xdc'
    ESC_ESC = b'\xdd'

    def __init__(self, device, baudrate=9600, **kwargs):
        self.ser = serial.Serial(device, baudrate=baudrate, **kwargs)

    def send(self, content: Union[OscMessage, OscBundle]) -> None:
        encoded = self.END
        encoded += content.dgram.replace(self.ESC, self.ESC + self.ESC_ESC).replace(self.END, self.ESC + self.ESC_END)
        encoded += self.END
        self.ser.write(encoded)

    def receive(self) -> Union[OscMessage, None]:
        buffer = b''
        while True:
            c = self.ser.read(1)
            if c is None:
                return None

            if c == self.END:
                if len(buffer):
                    break
                continue

            if c == self.ESC:
                c = self.ser.read(1)
                if c is None:
                    return None
                if c == self.ESC_END:
                    buffer += self.END
                elif c == self.ESC_ESC:
                    buffer += self.ESC
            else:
                buffer += c

        return OscMessage(buffer)
