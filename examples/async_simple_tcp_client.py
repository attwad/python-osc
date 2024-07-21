"""Small example Asynchronous OSC TCP client

This program listens for incoming messages in one task, and
sends 10 random values between 0.0 and 1.0 to the /filter address,
waiting for 1 seconds between each value in a second task.
"""
import argparse
import asyncio
import random
import sys

from pythonosc import tcp_client


async def get_messages(client):
    async for msg in client.get_messages(60):
        print(msg)


async def send_messages(client):
    for x in range(10):
        r = random.random()
        print(f"Sending /filter {r}")
        await client.send_message("/filter", r)
        await asyncio.sleep(1)


async def init_main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1",
                        help="The ip of the OSC server")
    parser.add_argument("--port", type=int, default=5005,
                        help="The port the OSC server is listening on")
    parser.add_argument("--mode", default="1.1",
                        help="The OSC protocol version of the server (default is 1.1)")
    args = parser.parse_args()

    async with tcp_client.AsyncSimpleTCPClient(args.ip, args.port, mode=args.mode) as client:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(get_messages(client))
            tg.create_task(send_messages(client))

if sys.version_info >= (3, 7):
    asyncio.run(init_main())
else:
    # TODO(python-upgrade): drop this once 3.6 is no longer supported
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(init_main())
    event_loop.close()
