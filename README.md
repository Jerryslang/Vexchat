an encrypted chatroom that uses the public hack.chat wss layered with aes256 encryption

(windows is not supported, seems to be some strange issues with websockets)

install requirements:

```bash
pip install -r requirements.txt
```

generate key/channel:

```bash
python3 ./client.py --keygen
```
