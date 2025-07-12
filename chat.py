import asyncio, websockets, json, os, string, sys
from utils import get_config, colored, encrypt, decrypt

if '--keygen' in sys.argv:
    aestemp = os.urandom(32).hex()
    charset = string.ascii_letters + string.digits
    channel = ''.join(charset[b % len(charset)] for b in os.urandom(32))
    print(f'aes256: {aestemp}\nchannel: {channel}')
    exit()

def reload_config():
    global WS_URL, CHANNEL, USERNAME, ENABLE_INPUT, ENABLE_COLOR, ENABLE_ENCRYPTION, ENCRYPTION_KEY, CLIENT_SIDE_COLOR
    WS_URL, CHANNEL, USERNAME, ENABLE_INPUT, ENABLE_COLOR, ENABLE_ENCRYPTION, ENCRYPTION_KEY, CLIENT_SIDE_COLOR = get_config()

reload_config()

if ENABLE_ENCRYPTION:
    trueuser = decrypt(ENCRYPTION_KEY, USERNAME) # (get_config encrypts username this decrypts it) seems bad but also acts as a test to see if encryption / decryption is working
else:
    trueuser = USERNAME

if not ENABLE_COLOR:
    def colored(text, color): # reroutes the coloring function to just print text as is if color mode is disabled
        return text

async def main():
    async with websockets.connect(WS_URL) as ws:
        join_msg = {"cmd": "join", "channel": CHANNEL, "nick": USERNAME}
        await ws.send(json.dumps(join_msg))

        async def send_loop(): # handles input loop and outgoing messages
            while True:
                if not ENABLE_INPUT: # hotswap config file fix for input disabling
                    break
                print(colored(f"{trueuser}: ", CLIENT_SIDE_COLOR), end='', flush=True)
                line = await asyncio.to_thread(input)
                if ENABLE_ENCRYPTION:
                    line = encrypt(ENCRYPTION_KEY, line) # encrypts your message
                if line.strip() and not line.startswith('!'):
                    await ws.send(json.dumps({"cmd": "chat", "text": line}))
                else:
                    if line == '!config':
                        reload_config()

        send_task = asyncio.create_task(send_loop()) if ENABLE_INPUT else None

        async for message in ws:
            data = json.loads(message)
            if data.get('nick') != USERNAME:
                cmd = data.get("cmd")

                if cmd == "onlineAdd":
                    user = data.get("nick")
                    if ENABLE_ENCRYPTION:
                        user = decrypt(ENCRYPTION_KEY, user)
                    print(f"User joined: {user}")

                elif cmd == "chat":
                    user = data.get("nick")
                    text = data.get("text")
                    color = data.get("color", "ffffff")
                    if ENABLE_ENCRYPTION:
                        # decrypt in seperate try/fail blocks so if text is encrypted and user isnt text still gets decrypted
                        try:
                            user = decrypt(ENCRYPTION_KEY, user)
                        except Exception:
                            pass

                        try:
                            text = decrypt(ENCRYPTION_KEY, text)
                        except Exception:
                            pass


                    content = f'{user}: {text}'
                    print(colored(f'\n{content}', color))
                    print(colored(f"{trueuser}: ", CLIENT_SIDE_COLOR), end='', flush=True) # prompt bug fix to print "username: " after processing a message

        if send_task:
            send_task.cancel()

asyncio.run(main())
