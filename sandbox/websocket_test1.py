import asyncio
import datetime
import random
import websockets

# put this state here to test that state can be shared across calls to time()
state = {"value": 0}

async def time(websocket, path):
    while True:
        print(state)
        now = datetime.datetime.utcnow().isoformat() + "Z" + f" {state['value']}"
        await websocket.send(now)
        await asyncio.sleep(random.random() * 3)
        state['value'] += 1

start_server = websockets.serve(time, "127.0.0.1", 5678)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
