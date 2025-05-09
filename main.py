from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit
from PyQt5.QtWidgets import QApplication
from py1337x import py1337x
from torrent import tr
from player import Player
from overlay import FullscreenApp
from logger import logging
from gitupdate import GitUpdater
import json
import psutil
import time
import signal
import subprocess
import threading
import os, sys
import pathlib
import logging
import sys

version = "1.0.0"  # default version, will be updated from version.txt

torrents = py1337x() 
updater = GitUpdater(github_owner="syntaxerror019", github_repo="PiRate", branch="main")

# change this depending on your QBittorrent software/ web ui api version...
tor = tr(use_old_api=False)

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'cache.json')
SETTINGS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'settings.json')
VERSION = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'version.txt')

settings = {}

items = {}
extra = {}

update_available = False

app = Flask(__name__)
socketio = SocketIO(app)
player = Player()

# serve the main page
@app.route('/')
def index():
    return render_template('index.html', version=version)

@app.route('/legal')
def legal():
    return render_template('legal.html')

@socketio.on('connect')
def test_connect():
    global update_available
    update_available, details = updater.check_for_updates()
    if update_available:
        logging.info("Update available!")
        emit('update', {'data': details})
        
    logging.info('Client connected')

@socketio.on('trending')
def handle_trending():
    logging.info("Received trending request")
    if items and extra:
        emit('trending_res', {'data': items, 'extra': extra})
    else:
        emit('trending_res', {'data': 'null', 'extra': 'null'})

@socketio.on('torrent')
def handle_torrent(url):
    logging.info("Received torrent request")   
    if not tor.download_torrent(url):
        logging.error("Failed to download torrent from URL: %s", url)
        emit('torrent_res', {'data': False})
    else:
        logging.info("Torrent download started successfully from URL: %s", url)
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
    
@socketio.on('update_now')
def handle_update_res():
    logging.info("Updating client now!")
    if update_available:
        updater.update_if_available()
        emit('update_now_res', {'data': True})
    else:
        emit('update_now_res', {'data': False})
        
    #os.execv(sys.executable, ['python3'] + sys.argv)
    restart_now()

@socketio.on('pause_torrent')
def handle_pause(id):
    logging.info("Received pause request")
    tor.pause(id)

@socketio.on('resume_torrent')
def handle_resume(id):
    logging.info("Received resume request")
    tor.resume(id)

@socketio.on('delete_torrent')
def handle_delete(id):
    logging.info("Received delete request")
    tor.delete(id)

# Media Controls
@socketio.on('watch')
def handle_watch(id):
    logging.info("Received watch request")
    logging.info(id)
    files = tor.torrent_status()
    file = tor.get_file_path(id, files)
    logging.info("THE TORRENT FILE IS: %s", file)
    player.set_media(file)
    player.play()
    emit('watch_res', {'data': file})

@socketio.on('pause')
@socketio.on('play')
def handle_pause():
    logging.info("Received pause/play request")
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
        logging.info("FFW")
        player.fast_forward(60)
    else:
        player.fast_forward(10)
        logging.info("FW")
    last_fast_forward_time = current_time
    fast_forward_count += 1
    
@socketio.on('rewind')
def handle_rewind():
    global rewind_count, last_rewind_time
    current_time = time.time()
    if current_time - last_rewind_time < 1/3:
        logging.info("RRW")
        player.rewind(60)
    else:
        player.rewind(10)
        logging.info("RW")
    last_rewind_time = current_time
    rewind_count += 1

@socketio.on('stop')
def handle_stop():
    logging.info("Received stop request")
    player.stop_and_close()

@socketio.on('enable_cc')
def handle_enable_cc():
    logging.info("Received enable CC request")
    player.enable_subtitles()

@socketio.on('disable_cc')
def handle_disable_cc():
    logging.info("Received disable CC request")
    player.disable_subtitles()

def setup():
    global items, extra, settings, version
    
    with open(VERSION, "r") as f:
        version = f.read().strip()
        
    logging.critical(f"PiRate v{version} - syntaxerror019")
    
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

    if not tor.check_connection():
        logging.error("Failed to connect to QBittorrent. Please check your settings and ensure QBittorrent is running.")
        raise Exception("Failed to connect to QBittorrent. Please check your settings and ensure QBittorrent is running.")
    

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
        
        
def signal_handler(sig, frame):
    logging.critical("Shutting down...")

    socketio.stop()

    for thread in threading.enumerate():
        if thread is not threading.main_thread():
            logging.info(f"Stopping thread: {thread.name}")
            thread.join(timeout=1)

    if player.is_playing():
        player.stop_and_close()

    app.quit()
    os._exit(0)
    
    
def restart_now():
    logging.critical("Restarting now...")

    socketio.stop()

    for thread in threading.enumerate():
        if thread is not threading.main_thread():
            logging.info(f"Stopping thread: {thread.name}")
            thread.join(timeout=1)

    if player.is_playing():
        player.stop_and_close()
        
    #os.execv(sys.executable, ['python3'] + sys.argv)
    
    try:
        process = psutil.Process(os.getpid())

        for handler in process.open_files() + process.connections():
            os.close(handler.fd)
    except Exception as e:
        print(e)

    python = sys.executable
    os.execl(python, python, *sys.argv)


# Start the SocketIO server
if __name__ == '__main__':
    setup()
    
    signal.signal(signal.SIGINT, signal_handler)  # Handle keyboard interrupt gracefully
    
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
        signal_handler(signal.SIGINT, None)  # Handle keyboard interrupt gracefully
    except Exception as e:
        logging.error("An error occurred: %s", str(e))