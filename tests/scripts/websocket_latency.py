"""Measure the authenticated recognition stream without logging credentials."""

import argparse
import asyncio
import base64
import json
import os
import statistics
import time

import cv2
import numpy as np
import websockets


def browser_payload(image_path):
    if image_path:
        image = cv2.imread(image_path)
        if image is None:
            raise RuntimeError(f"Cannot read image: {image_path}")
    else:
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(
            image,
            "FaceGuard latency probe",
            (80, 240),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )
    encoded, buffer = cv2.imencode(".jpg", image)
    if not encoded:
        raise RuntimeError("Cannot encode the browser-mode probe frame")
    payload = base64.b64encode(buffer).decode("ascii")
    return f"data:image/jpeg;base64,{payload}"


async def measure(args):
    payload = browser_payload(args.image) if args.camera_source == "browser" else None
    protocols = ["faceguard.jwt", f"bearer.{args.token}"]
    durations = []

    print(f"Connecting to {args.uri} in {args.camera_source} mode")
    async with websockets.connect(args.uri, subprotocols=protocols) as websocket:
        if websocket.subprotocol != "faceguard.jwt":
            raise RuntimeError("Backend did not negotiate the FaceGuard protocol")

        for index in range(args.iterations):
            started_at = time.perf_counter()
            if payload is not None:
                await websocket.send(payload)
            response = json.loads(await websocket.recv())
            elapsed_ms = (time.perf_counter() - started_at) * 1000.0
            durations.append(elapsed_ms)
            print(
                f"{index + 1}: {elapsed_ms:.1f} ms; "
                f"status={response.get('status')!r}; "
                f"frame={response.get('frame_width')}x{response.get('frame_height')}; "
                f"preview={'frame' in response}"
            )

    print(
        f"mean={statistics.fmean(durations):.1f} ms; "
        f"min={min(durations):.1f} ms; max={max(durations):.1f} ms; "
        f"preview_fps={1000.0 / statistics.fmean(durations):.2f}"
    )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--uri",
        default=os.environ.get("FACEGUARD_WS_URL", "ws://127.0.0.1:8000/ws/recognize"),
    )
    parser.add_argument("--token", default=os.environ.get("FACEGUARD_JWT"))
    parser.add_argument(
        "--camera-source",
        choices=("browser", "backend"),
        default=os.environ.get("CAMERA_SOURCE", "backend"),
    )
    parser.add_argument("--image")
    parser.add_argument("--iterations", type=int, default=10)
    args = parser.parse_args()
    if not args.token:
        parser.error("pass --token or set FACEGUARD_JWT")
    if args.iterations <= 0:
        parser.error("--iterations must be positive")
    return args


if __name__ == "__main__":
    asyncio.run(measure(parse_args()))
