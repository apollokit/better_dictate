import asyncio
import datetime
import random
import json
import websockets
import threading


def run_websocket_server():
    asyncio.set_event_loop(asyncio.new_event_loop())

    active = False

    async def transact(websocket, path):
        nonlocal active
        while True:
            # now = datetime.datetime.utcnow().isoformat() + "Z"
            # await websocket.send(now)
            # await asyncio.sleep(random.random() * 3)

            msg = json.loads(await websocket.recv())
            print(msg)
            
            if active:
                print(f"saw: {msg}")

            if msg['cmd'] == "hello":
                await websocket.send('{"cmd": "start"}')
                print('saw start')
                active = True
            elif msg['cmd'] == "end":
                print('saw end')
                active = False


    start_server = websockets.serve(transact, "127.0.0.1", 5678)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

websocket_thread = threading.Thread(target=run_websocket_server, args=())
websocket_thread.start()
