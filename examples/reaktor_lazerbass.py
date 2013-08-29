"""Example to drive/show reaktor's lazerbass instrument in pygame."""
import argparse
import pygame
import multiprocessing
import queue
import logging

from pygame.locals import *

from pythonosc import dispatcher
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
    self._screen = pygame.display.set_mode((640, 480))  # FULLSCREEN
    running = True
    dirty = True
    # OSC controlled parameters.
    self._beating = 2.0
    while running:
      for event in pygame.event.get():
        if event.type == QUIT:
          running = False
      try:
        beating = self._bq.get(False)
        self._beating = beating
        dirty = True
      except queue.Empty:
        pass
      if dirty:
        self._screen.fill(_BLACK)
        # left, top, width, height
        pygame.draw.rect(
            self._screen, _WHITE, [10, 10, 50, 16 * 10], 2)
        pygame.draw.rect(
            self._screen, _WHITE, [10, 170, 50, -int(self._beating * 100)])
        pygame.display.flip()
        dirty = False
    pygame.quit()


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument(
      "--server_ip", default="127.0.0.1", help="The ip of the OSC server")
  parser.add_argument(
      "--server_port", type=int, default=8000,
      help="The port the OSC server is listening on")
  #parser.add_argument("--client_ip",
  #    default="127.0.0.1", help="The ip to listen on")
  #parser.add_argument("--client_port",
  #    type=int, default=5005, help="The port to listen on")
  args = parser.parse_args()

  #client = udp_client.UDPClient(args.client_ip, args.client_port)

  bq = multiprocessing.Queue()
  reaktor = ReaktorDisplay(bq)

  dispatcher = dispatcher.Dispatcher()
  dispatcher.map("/debug", logging.debug)
  dispatcher.map("/beating", bq.put)

  server = osc_server.ThreadingOSCUDPServer(
      (args.server_ip, args.server_port), dispatcher)
  logging.info("Serving on {}".format(server.server_address))

  # Exit thread when the main thread terminates.
  reaktor.daemon = True
  reaktor.start()

  server.serve_forever()
