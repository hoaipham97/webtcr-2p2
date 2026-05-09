import asyncio
import os
from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    RTCConfiguration,
    RTCBundlePolicy,
    RTCIceServer,
)

config = RTCConfiguration(
    iceServers=[RTCIceServer(urls="stun:stun.l.google.com:19302")],
    bundlePolicy=RTCBundlePolicy.MAX_BUNDLE,
)


def read_sdp(prompt):
    print(prompt)
    print("Paste SDP, then type END and press Enter:")

    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)

    return "\r\n".join(lines) + "\r\n"


async def main():
    pc = RTCPeerConnection(config)
    channel = pc.createDataChannel("file")

    filename = "demo.json"
    done = asyncio.Event()

    async def send_file():
        channel.send(f"FILENAME:{os.path.basename(filename)}")

        with open(filename, "rb") as f:
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

    print("OFFER:")
    print(pc.localDescription.sdp)

    answer = read_sdp("Paste ANSWER SDP:")

    await pc.setRemoteDescription(
        RTCSessionDescription(sdp=answer, type="answer")
    )

    print("Connected!")

    await done.wait()
    await asyncio.sleep(1)
    await pc.close()


asyncio.run(main())