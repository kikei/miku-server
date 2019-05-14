# Miku server

Have Miku Hatsune speak anything on a Raspberry Pi with HTTP server.

For more details, refer my blog:
https://kikei.github.io/smart-home/2018/06/13/raspberry-miku.html.

## Technologies

- Python
- Flask
- uWSGI
- OpenJTalk
- Bluetooth
- Raspberry Pi

## How to install

### 1. Setup systemd service:

You can copy service file from uwsgi-miku.service.example:

```sh
$ cp uwsgi-miku.service.example uwsgi-miku.service
```

And you must set environment variables as following:

- PLAYLIST: Path of M3U8 playlist file. Miku chooses songs from it.
- SPEAKER_MAC: MAC address of external bluetooth speaker.

Then install and apply service:

```sh
# install uwsgi-miku.service /etc/systemd/system/
# systemctl daemon-reload
```

### 2. Start service

```sh
# systemctl start uwsgi-miku
```

### 3. Run

Get miku to sing!

```sh
$ curl -XPOST "http://localhost:5000/sing"
```
