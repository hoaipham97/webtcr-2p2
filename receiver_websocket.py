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

SIGNALING_WS = "wss://webtcr-2p2-production.up.railway.app/ws/receiver"

config = RTCConfiguration(
    iceServers=[RTCIceServer(urls="stun:stun.l.google.com:19302")],
    bundlePolicy=RTCBundlePolicy.MAX_BUNDLE,
)


async def main():
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

    async with websockets.connect(SIGNALING_WS) as ws:
        print("Receiver connected. Waiting for offer...")

        while True:
            raw = await ws.recv()
            data = json.loads(raw)

            if data.get("type") == "offer":
                await pc.setRemoteDescription(
                    RTCSessionDescription(
                        sdp=data["sdp"],
                        type="offer",
                    )
                )

                answer = await pc.createAnswer()
                await pc.setLocalDescription(answer)

                await ws.send(json.dumps({
                    "type": "answer",
                    "target": "sender",
                    "sdp": pc.localDescription.sdp,
                }))

                print("Answer sent. Waiting for file...")
                break

        await done.wait()
        await asyncio.sleep(1)
        await pc.close()


asyncio.run(main())