# core imports
from core.security import encrypt, decrypt, time_ago
from core.utils import structure_message

# standard imports
import asyncio, tomllib, json, time, os, platform

# non standard imports
import websockets

with open('config.toml', 'rb') as tconfig:
    config = tomllib.load(tconfig)

WS_URL = 'wss://hack.chat/chat-ws' # yeah it uses hack chat, cry about it
SUSPICIONS = []
CHANNEL = config['vexchat']['channel']
USERNAME = config['vexchat']['username']

# init message (sends a join message along with your operating system) 
# (only linux is officaly supported but could work on other systems and could be easily be modified to do so)
osname = platform.system().lower() # Windows, Linux, Darwin, ...BSD
INIT_MSG = structure_message(f'os:{osname} / has joined.,.')

if ' ' in USERNAME or not USERNAME:
    print('invalid username remove spaces')
    exit()

key_hex = config['aes']['key']

os.system('cls' if os.name == 'nt' else 'clear')

async def chat():
    async with websockets.connect(WS_URL) as ws:
        await ws.send(json.dumps({"cmd": "join", "channel": CHANNEL, "nick": USERNAME}))
        print(f"Connected to #{CHANNEL} as {USERNAME}")
        await ws.send(json.dumps({"cmd": "chat", "text": encrypt(key_hex, INIT_MSG)}))

        async def recv_loop():
            async for message in ws:
                try:
                    data = json.loads(message)
                    if data.get("cmd") == "chat":
                        nick = data["nick"]
                        text = decrypt(key_hex, data["text"])
                        sender = "(you)" if nick == USERNAME else nick

                        timestamp_str, _, message = text.partition("!*")
                        timestamp = int(float(timestamp_str))

                        if 'joined.,.' not in message:
                            print(f"[{time_ago(timestamp)}] {sender}: {message}")
                        else:
                            senders_os = message.split('os:')[1].split(' /')[0]
                            print(f"\033[32m{sender}: has joined on {senders_os}\033[0m")

                        if time_ago(timestamp, raw_seconds=True) > 5:
                            sus_temp = f'[WARNING] Possible replay attack detected on message: "{message}" from {sender}'
                            print(sus_temp)
                            SUSPICIONS.append(sus_temp)

                    elif data.get("cmd") in ("warn", "info"):
                        print(f"[System] {data['text']}")
                except Exception as e:
                    print(f"[!] Error decoding message: {e}")
                    print(f"[!] Raw message: {message}")

        async def input_loop():
            while True:
                raw_input = await asyncio.get_event_loop().run_in_executor(None, input, "> ")
                msg = raw_input.strip().replace('!*', '')
                if not msg:
                    continue
                msg = f"{time.time()}!*{msg}"
                enc = encrypt(key_hex, msg)
                await ws.send(json.dumps({"cmd": "chat", "text": enc}))

        await asyncio.gather(recv_loop(), input_loop())

try:
    asyncio.run(chat())
except KeyboardInterrupt:
    exit()
