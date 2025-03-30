from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit
from PyQt5.QtWidgets import QApplication
from py1337x import py1337x
from torrent import tr
from player import Player
from overlay import FullscreenApp
import json
import time
import threading
import os, sys
import pathlib

torrents = py1337x() 

# Change this depending on your QBittorrent software/ web ui api version...
tor = tr(use_old_api=False)

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'cache.json')
SETTINGS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'settings.json')

settings = {}

items = {}
extra = {}

app = Flask(__name__)
socketio = SocketIO(app)
player = Player()

# Serve the main page
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/legal')
def legal():
    return render_template('legal.html')

@socketio.on('connect')
def test_connect():
    print('Client connected')

@socketio.on('trending')
def handle_trending():
    print("Received trending request")
    if items and extra:
        emit('trending_res', {'data': items, 'extra': extra})
    else:
        emit('trending_res', {'data': 'null', 'extra': 'null'})

@socketio.on('torrent')
def handle_torrent(url):
    print("Received torrent request")   
    if not tor.download_torrent(url):
        emit('torrent_res', {'data': False})
    else:
        emit('torrent_res', {'data': True})

@socketio.on('status')
def handle_status():
    emit('status_res', {'data': tor.torrent_status()})

@socketio.on('search')
def handle_search(key):
    try:
        emit('search_res', torrents.search(query=key))
    except:
        emit('search_res', {'items': 'null'})

@socketio.on('details')
def handle_details(id):
    emit('details_res', {'data': torrents.info(torrentId=id), 'torrentId':id})

@socketio.on('pause_torrent')
def handle_pause(id):
    print("Received pause request")
    tor.pause(id)

@socketio.on('resume_torrent')
def handle_resume(id):
    print("Received resume request")
    tor.resume(id)

@socketio.on('delete_torrent')
def handle_delete(id):
    print("Received delete request")
    tor.delete(id)

# Media Controls
@socketio.on('watch')
def handle_watch(id):
    print("Received watch request")
    print(id)
    files = tor.torrent_status()
    file = tor.get_file_path(id, files)
    print("THE TORRENT FILE IS: ", file)
    player.set_media(file)
    player.play()
    emit('watch_res', {'data': file})

@socketio.on('pause')
@socketio.on('play')
def handle_pause():
    print("Received pause/play request")
    player.pause()

# Monitoring variables
fast_forward_count = 0
rewind_count = 0
last_fast_forward_time = 0
last_rewind_time = 0

@socketio.on('fast_forward')
def handle_fast_forward():
    global fast_forward_count, last_fast_forward_time
    current_time = time.time()
    if current_time - last_fast_forward_time < 1/3:
        print("FFW")
        player.fast_forward(60)
    else:
        player.fast_forward(10)
        print("FW")
    last_fast_forward_time = current_time
    fast_forward_count += 1
    
@socketio.on('rewind')
def handle_rewind():
    global rewind_count, last_rewind_time
    current_time = time.time()
    if current_time - last_rewind_time < 1/3:
        print("RRW")
        player.rewind(60)
    else:
        player.rewind(10)
        print("RW")
    last_rewind_time = current_time
    rewind_count += 1

@socketio.on('stop')
def handle_stop():
    print("Received stop request")
    player.stop_and_close()

@socketio.on('enable_cc')
def handle_enable_cc():
    print("Received enable CC request")
    player.enable_subtitles()

@socketio.on('disable_cc')
def handle_disable_cc():
    print("Received disable CC request")
    player.disable_subtitles()

def setup():
    global items, extra, settings
    if os.path.exists(SETTINGS):
        with open(SETTINGS, 'r') as f:
            settings = json.load(f)
    else:
        with open(SETTINGS, 'w') as f:
            settings = {'location': str(pathlib.Path.home() / 'Downloads' / 'PiRate-Downloads')}
            json.dump(settings, f)

    if os.path.exists(CACHE):
        with open(CACHE, 'r') as f:
            data = json.load(f)
            items = data['data']
            extra = data['extra']
    
    if settings['location']:
        tor.set_torrent_download_location(settings['location'], create=True)
    else:
        raise Exception("No download location set. Is the settings file missing?")

def background_task():
    global items, extra

    time.sleep(1800)

    while True:
        try:
            items_temp = torrents.trending(category='movies')['items']
        except:
            pass

        extra_temp = {}

        for item in items_temp:
            info = torrents.info(torrentId=item['torrentId'])
            entry = { item['torrentId']: info }
            extra_temp.update(entry)

        items = items_temp
        extra = extra_temp

        with open(CACHE, 'w') as f:
            json.dump({'data': items, 'extra': extra}, f)

        socketio.emit('trending_res', {'data': items, 'extra': extra})
        

# Start the SocketIO server
if __name__ == '__main__':
    setup()
    
    try:
        thread = threading.Thread(target=background_task)
        thread.daemon = True
        thread.start()
        
        socketio_thread = threading.Thread(target=lambda: socketio.run(app, debug=False, host='0.0.0.0', port=8080))
        socketio_thread.daemon = True
        socketio_thread.start()

        app = QApplication(sys.argv)
        window = FullscreenApp()
        sys.exit(app.exec_())

    except KeyboardInterrupt:
        print("Exiting...")
        if player.is_playing():
            player.stop_and_close()
        sys.exit(0)