import asyncio
import websockets
import base64
import time
import urllib.request
import cv2
import numpy as np
import json


async def test_latency():
    url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/lena.jpg"
    print("Downloading sample image...")
    req = urllib.request.urlopen(url)
    arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    _, buffer = cv2.imencode(".jpg", img)
    b64_str = base64.b64encode(buffer).decode("utf-8")
    payload = f"data:image/jpeg;base64,{b64_str}"

    uri = "ws://localhost:8000/ws/recognize"
    print(f"Connecting to {uri}...")

    # Do 5 iterations to see average latency and warm up
    async with websockets.connect(uri) as websocket:
        print("Connected.")

        for i in range(5):
            print(f"\nIteration {i+1}...")
            start = time.perf_counter()
            await websocket.send(payload)
            response = await websocket.recv()
            end = time.perf_counter()

            data = json.loads(response)
            status = data.get("status")
            print(f"Status: {status}")
            print(f"Latency: {(end - start) * 1000:.2f} ms")

            # Wait a bit before next frame
            await asyncio.sleep(0.5)


if __name__ == "__main__":
    asyncio.run(test_latency())
