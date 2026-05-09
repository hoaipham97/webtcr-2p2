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

    # offer_sdp = read_sdp("Paste OFFER SDP:")
    with open("offer.txt", "r", encoding="utf-8") as f:
        offer_sdp = f.read()

    await pc.setRemoteDescription(
        RTCSessionDescription(sdp=offer_sdp, type="offer")
    )

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    print("ANSWER SDP:")
    print(pc.localDescription.sdp)

    await done.wait()
    await asyncio.sleep(1)
    await pc.close()


asyncio.run(run_receiver())