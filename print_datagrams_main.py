"""A simple program that displays datagrams received on a port."""

import argparse
import socket


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument(
      "--ip",
      default="127.0.0.1",
      help="The ip to listen on")
  parser.add_argument(
      "--port",
      type=int,
      default=5005,
      help="The port to listen on")

  args = parser.parse_args()
  _PrintOscMessages(args.ip, args.port)


def _PrintOscMessages(ip, port):
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.bind((ip, port))
  print("Listening for UDP packets on {0}:{1} ...".format(ip, port))
  while True:
    data, _ = sock.recvfrom(1024)
    print("%s" % data)


if __name__=="__main__":
  main()
