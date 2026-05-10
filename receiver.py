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

SIGNALING_SERVER = "https://xxx.up.railway.app"

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


async def run_receiver():
    pc = RTCPeerConnection(config)
    done = asyncio.Event()

    @pc.on("datachannel")
    def on_channel(channel):
        print("DataChannel received:", channel.label)

        f = None

        @channel.on("message")
        def on_msg(msg):
            nonlocal f

            if isinstance(msg, str) and msg.startswith("FILENAME:"):
                original_name = msg.replace("FILENAME:", "", 1)
                save_name = "receiver_" + os.path.basename(original_name)

                f = open(save_name, "wb")
                print("Saving as:", save_name)
                return

            if msg == b"END":
                if f:
                    f.close()

                print("Received!")
                done.set()
                return

            if f:
                f.write(msg)

    print("Waiting for OFFER...")
    offer_sdp = wait_sdp("/offer")

    await pc.setRemoteDescription(
        RTCSessionDescription(sdp=offer_sdp, type="offer")
    )

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    print("Posting ANSWER to signaling server...")
    post_sdp("/answer", pc.localDescription.sdp)

    print("Waiting for file...")

    await done.wait()
    await asyncio.sleep(1)
    await pc.close()


asyncio.run(run_receiver())