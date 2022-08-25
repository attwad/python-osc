"""Example to drive/show reaktor's lazerbass instrument in pygame."""
import argparse
import pygame
import multiprocessing
import queue
import logging

from typing import Tuple

from pygame.constants import QUIT

from pythonosc.dispatcher import Dispatcher
from pythonosc import osc_server

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] (%(threadName)-10s) %(message)s',
)

_BLACK = pygame.Color(0, 0, 0)
_WHITE = pygame.Color(255, 255, 255)


class ReaktorDisplay(multiprocessing.Process):
    def __init__(self, bq):
        multiprocessing.Process.__init__(self)
        self._bq = bq

    def run(self):
        pygame.init()
        font = pygame.font.SysFont("monospace", 15)
        screen = pygame.display.set_mode((640, 480))  # FULLSCREEN
        running = True
        dirty = True
        # OSC controlled parameters.
        self._parameters = {
            'beating': 0.0,
            'blocks': 0.0,
            'basic_Model': 0.0,
            'Do!': 0.0,
        }
        while running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
            if dirty:
                screen.fill(_BLACK)
                # Draw a gauge using rectangles.
                # Left, top, width, height.
                pygame.draw.rect(
                    screen, _WHITE, [10, 10, 50, 100], 2)
                pygame.draw.rect(
                    screen, _WHITE, [10, 110, 50, -int(self._parameters['beating'] * 100)])

                # Draw a button-like square for on/off display.
                pygame.draw.rect(
                    screen, _WHITE, [10, 200, 50, 50], 2)
                pygame.draw.rect(
                    screen, _WHITE, [10, 200, 50, 50 if self._parameters['blocks'] >= 0.5 else 0])

                # Show actual values.
                for index, [key, val] in enumerate(self._parameters.items()):
                    label = font.render("{0}: {1}".format(key, val), 1, _WHITE)
                    screen.blit(label, (200, index * 15))
                pygame.display.flip()
                dirty = False
            try:
                what, value = self._bq.get(True)
                self._parameters[what] = value
                dirty = True
                logging.debug('Received new value {0} = {1}'.format(what, value))
            except queue.Empty:
                running = False
        pygame.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--server_ip", default="0.0.0.0",
        help="The ip to listen to for reaktor OSC messages")
    parser.add_argument(
        "--server_port", type=int, default=8000,
        help="The port to listen on for reaktor OSC messages")
    # parser.add_argument("--client_ip",
    #    default="127.0.0.1", help="The ip to listen on")
    # parser.add_argument("--client_port",
    #    type=int, default=5005, help="The port to listen on")
    args = parser.parse_args()

    # client = udp_client.UDPClient(args.client_ip, args.client_port)

    bq = multiprocessing.Queue()  # type: multiprocessing.Queue[Tuple[str, float]]
    reaktor = ReaktorDisplay(bq)


    def put_in_queue(args, value):
        """Put a named argument in the queue to be able to use a single queue."""
        bq.put((args[0], value))


    dispatcher = Dispatcher()
    dispatcher.map("/debug", logging.debug)
    dispatcher.map("/beating", put_in_queue, "beating")
    dispatcher.map("/blocks", put_in_queue, "blocks")
    dispatcher.map("/basic_Model", put_in_queue, "basic_Model")
    dispatcher.map("/Do!", put_in_queue, "Do!")

    server = osc_server.ThreadingOSCUDPServer(
        (args.server_ip, args.server_port), dispatcher)
    logging.info("Serving on {}".format(server.server_address))

    # Exit thread when the main thread terminates.
    reaktor.daemon = True
    reaktor.start()

    server.serve_forever()
