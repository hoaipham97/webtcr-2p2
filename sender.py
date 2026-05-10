import asyncio
import os
import time
import requests

from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    RTCConfiguration,
    RTCBundlePolicy,
    RTCIceServer,
)

SIGNALING_SERVER = "https://webtcr-2p2-production.up.railway.app"
FILE_TO_SEND = "demo.json"

config = RTCConfiguration(
    iceServers=[RTCIceServer(urls="stun:stun.l.google.com:19302")],
    bundlePolicy=RTCBundlePolicy.MAX_BUNDLE,
)


def post_sdp(path, sdp):
    res = requests.post(
        f"{SIGNALING_SERVER}{path}",
        json={"sdp": sdp},
        timeout=10,
    )
    res.raise_for_status()


def wait_sdp(path):
    while True:
        res = requests.get(f"{SIGNALING_SERVER}{path}", timeout=10)
        res.raise_for_status()

        sdp = res.json().get("sdp")
        if sdp:
            return sdp

        print(f"Waiting for {path}...")
        time.sleep(2)


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

    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    print("Posting OFFER to signaling server...")
    post_sdp("/offer", pc.localDescription.sdp)

    print("Waiting for ANSWER...")
    answer_sdp = wait_sdp("/answer")

    await pc.setRemoteDescription(
        RTCSessionDescription(sdp=answer_sdp, type="answer")
    )

    print("Connected!")

    await done.wait()
    await asyncio.sleep(1)
    await pc.close()


asyncio.run(main())