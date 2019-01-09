from pythonosc.dispatcher import Dispatcher
from typing import List, Any

dispatcher = Dispatcher()


def set_filter(address: str, *args: List[Any]) -> None:
    # We expect two float arguments
    if not len(args) == 2 or type(args[0]) is not float or type(args[1]) is not float:
        return

    # Check that address starts with filter
    if not address[:-1] == "/filter":  # Cut off the last character
        return

    value1 = args[0]
    value2 = args[1]
    filterno = address[-1]
    print(f"Setting filter {filterno} values: {value1}, {value2}")


dispatcher.map("/filter*", set_filter)  # Map wildcard address to set_filter function

# Set up server and client for testing
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient

server = BlockingOSCUDPServer(("127.0.0.1", 1337), dispatcher)
client = SimpleUDPClient("127.0.0.1", 1337)

# Send message and receive exactly one message (blocking)
client.send_message("/filter1", [1., 2.])
server.handle_request()

client.send_message("/filter8", [6., -2.])
server.handle_request()
