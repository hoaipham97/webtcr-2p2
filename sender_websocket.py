import asyncio
import json
import os
import websockets

from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    RTCConfiguration,
    RTCBundlePolicy,
    RTCIceServer,
)

SIGNALING_WS = "wss://webtcr-2p2-production.up.railway.app/ws/sender"
FILE_TO_SEND = "demo.json"

config = RTCConfiguration(
    iceServers=[RTCIceServer(urls="stun:stun.l.google.com:19302")],
    bundlePolicy=RTCBundlePolicy.MAX_BUNDLE,
)


async def main():
    pc = RTCPeerConnection(config)
    channel = pc.createDataChannel("file")
    done = asyncio.Event()

    async def send_file():
        filename = os.path.basename(FILE_TO_SEND)
        channel.send(f"FILENAME:{filename}")

        with open(FILE_TO_SEND, "rb") as f:
            while chunk := f.read(16384):
                channel.send(chunk)
                await asyncio.sleep(0)

        channel.send(b"END")
        print("Sent!")
        done.set()

    @channel.on("open")
    def on_open():
        print("DataChannel opened")
        asyncio.create_task(send_file())

    async with websockets.connect(SIGNALING_WS) as ws:
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        await ws.send(json.dumps({
            "type": "offer",
            "target": "receiver",
            "sdp": pc.localDescription.sdp,
        }))

        print("Offer sent. Waiting for answer...")

        while True:
            raw = await ws.recv()
            data = json.loads(raw)

            if data.get("type") == "answer":
                await pc.setRemoteDescription(
                    RTCSessionDescription(
                        sdp=data["sdp"],
                        type="answer",
                    )
                )
                print("Connected!")
                break

        await done.wait()
        await asyncio.sleep(1)
        await pc.close()


asyncio.run(main())