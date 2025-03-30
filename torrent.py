import requests, os, re, time

TORRENT_BASE_URL = None
TORRENT_VERSION_ENDPOINT = None
TORRENT_ADD_ENDPOINT = None
TORRENT_STATUS_ENDPOINT = None
TORRENT_PAUSE_ENDPOINT = None
TORRENT_RESUME_ENDPOINT = None
TORRENT_DELETE_ENDPOINT = None

V4_TORRENT_BASE_URL = 'http://localhost:5000'
V4_TORRENT_VERSION_ENDPOINT = '/api/v2/app/version'
V4_TORRENT_ADD_ENDPOINT = '/api/v2/torrents/add'
V4_TORRENT_STATUS_ENDPOINT = '/api/v2/sync/maindata'
V4_TORRENT_PAUSE_ENDPOINT = '/api/v2/torrents/pause'
V4_TORRENT_RESUME_ENDPOINT = '/api/v2/torrents/resume'
V4_TORRENT_DELETE_ENDPOINT = '/api/v2/torrents/delete'

V3_TORRENT_BASE_URL = 'http://localhost:5000'
V3_TORRENT_VERSION_ENDPOINT = '/version/api'
V3_TORRENT_ADD_ENDPOINT = '/command/download'
V3_TORRENT_STATUS_ENDPOINT = '/sync/maindata'
V3_TORRENT_PAUSE_ENDPOINT = '/command/pause'
V3_TORRENT_RESUME_ENDPOINT = '/command/resume'
V3_TORRENT_DELETE_ENDPOINT = '/command/deletePerm'


def split_keywords(name):
    return re.split(r'[.\s\-]+', name.lower())


class tr:
    def __init__(self, url=None, endpoint=None, use_old_api=False):
        global TORRENT_BASE_URL, TORRENT_VERSION_ENDPOINT, TORRENT_ADD_ENDPOINT, TORRENT_STATUS_ENDPOINT, TORRENT_PAUSE_ENDPOINT, TORRENT_RESUME_ENDPOINT, TORRENT_DELETE_ENDPOINT
        global V3_TORRENT_BASE_URL, V3_TORRENT_VERSION_ENDPOINT, V3_TORRENT_ADD_ENDPOINT, V3_TORRENT_STATUS_ENDPOINT, V3_TORRENT_PAUSE_ENDPOINT, V3_TORRENT_RESUME_ENDPOINT, V3_TORRENT_DELETE_ENDPOINT
        global V4_TORRENT_BASE_URL, V4_TORRENT_VERSION_ENDPOINT, V4_TORRENT_ADD_ENDPOINT, V4_TORRENT_STATUS_ENDPOINT, V4_TORRENT_PAUSE_ENDPOINT, V4_TORRENT_RESUME_ENDPOINT, V4_TORRENT_DELETE_ENDPOINT

        if url:
            self.url = url
            V3_TORRENT_BASE_URL = url
            V4_TORRENT_BASE_URL = url
        
        if endpoint:
            self.endpoint = endpoint
            V3_TORRENT_VERSION_ENDPOINT = endpoint
            V4_TORRENT_VERSION_ENDPOINT = endpoint

        if use_old_api:
            self.use_old_api = True
            TORRENT_BASE_URL = V3_TORRENT_BASE_URL
            TORRENT_VERSION_ENDPOINT = V3_TORRENT_VERSION_ENDPOINT
            TORRENT_ADD_ENDPOINT = V3_TORRENT_ADD_ENDPOINT
            TORRENT_STATUS_ENDPOINT = V3_TORRENT_STATUS_ENDPOINT
            TORRENT_PAUSE_ENDPOINT = V3_TORRENT_PAUSE_ENDPOINT
            TORRENT_RESUME_ENDPOINT = V3_TORRENT_RESUME_ENDPOINT
            TORRENT_DELETE_ENDPOINT = V3_TORRENT_DELETE_ENDPOINT
        else:
            self.use_old_api = False
            TORRENT_BASE_URL = V4_TORRENT_BASE_URL
            TORRENT_VERSION_ENDPOINT = V4_TORRENT_VERSION_ENDPOINT
            TORRENT_ADD_ENDPOINT = V4_TORRENT_ADD_ENDPOINT
            TORRENT_STATUS_ENDPOINT = V4_TORRENT_STATUS_ENDPOINT
            TORRENT_PAUSE_ENDPOINT = V4_TORRENT_PAUSE_ENDPOINT
            TORRENT_RESUME_ENDPOINT = V4_TORRENT_RESUME_ENDPOINT
            TORRENT_DELETE_ENDPOINT = V4_TORRENT_DELETE_ENDPOINT

        self.location = None

        connection_attempts = 0
        
        # attempt to connect to the client over the span of 15 seconds
        
        while connection_attempts < 3:
            try:
                # Test connection to the torrent client
                res = requests.get(TORRENT_BASE_URL + TORRENT_VERSION_ENDPOINT)
                if res.status_code == 200:
                    break
                else:
                    raise ConnectionError("Non 200 status code. Is the right URL and port set?")
            except requests.exceptions.ConnectionError:
                connection_attempts += 1
                if connection_attempts >= 3:
                    raise ConnectionError("Connection error. Is qbittorrent running? Is the right URL and port set?")
                print(f"Connection attempt {connection_attempts} failed. Retrying in 5 seconds...")
                time.sleep(5)


    def set_torrent_download_location(self, location, create=False):
        if not os.path.exists(location):
            if not create:
                return False
            os.makedirs(location)
        
        self.location = location 
        return True


    def download_torrent(self, url):
        print("Downloading to:", self.location)
        data = {
            'urls': url,
            'autoTMM': 'false',
            'savepath': self.location,
            'cookie': '',
            'rename': '',
            'category': '',
            'paused': 'false',
            'stopCondition': 'None',
            'contentLayout': 'NoSubfolder',
            'dlLimit': 'NaN',
            'upLimit': 'NaN'
        }

        try:
            res = requests.post(TORRENT_BASE_URL + TORRENT_ADD_ENDPOINT, data=data)
        except requests.exceptions.ConnectionError: 
            raise ConnectionError("Connection error. Is qbittorrent running? Is the right URL and port set?")

        if res.status_code == 200:
            return True
        return False
    
    
    def torrent_status(self):
        try:
            res = requests.get(TORRENT_BASE_URL + TORRENT_STATUS_ENDPOINT)
            res.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Connection error. Is qbittorrent running? Is the right URL used?")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP error occurred: {e}")
        
        data = res.json()

        torrents = data.get('torrents', {})

        data = []

        for torrent_hash, torrent in torrents.items():
            entry = {
                'hash': torrent_hash,
                'name': torrent['name'],
                'state': torrent['state'],
                'uri': torrent['magnet_uri'],
                'dlspeed': torrent['dlspeed'],
                'eta': torrent['eta'],
                'progress': torrent['progress']
            }
            data.append(entry)
        
        return data
    
    
    def pause(self, torrent_hash):
        if not torrent_hash:
            return False
        
        if self.use_old_api:
            data = {'hash': torrent_hash}
        else:
            data = {'hashes': torrent_hash }

        try:
            res = requests.post(TORRENT_BASE_URL + TORRENT_PAUSE_ENDPOINT, data=data)
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Connection error. Is qbittorrent running? Is the right URL and port set?")

        if res.status_code == 200:
            return True
        return False
    
    
    def resume(self, torrent_hash):
        if not torrent_hash:
            return False
        
        if self.use_old_api:
            data = {'hash': torrent_hash}
        else:
            data = {'hashes': torrent_hash }

        try:
            res = requests.post(TORRENT_BASE_URL + TORRENT_RESUME_ENDPOINT, data=data)
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Connection error. Is qbittorrent running? Is the right URL and port set?")

        if res.status_code == 200:
            return True
        return False
    
    
    def delete(self, torrent_hash, delete_files=True):
        if not torrent_hash:
            return False
        
        if self.use_old_api:
            data = {'hashes': torrent_hash}
        else:
            data = {
                'hashes': torrent_hash,
                'deleteFiles': delete_files
            }

        try:
            res = requests.post(TORRENT_BASE_URL + TORRENT_DELETE_ENDPOINT, data=data)
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Connection error. Is qbittorrent running? Is the right URL and port set?")
        
        if res.status_code == 200:
            return True
        return False
    

    def get_file_path(self, id, torrents):
        video_extensions = ('.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv')     
        for entry in torrents:
            print(f"Checking entry: {entry['hash']} against id: {id}")
            if entry['hash'] == id:
                entry_keywords = split_keywords(entry['name'])
                
                for root, dirs, files in os.walk(self.location):
                    for file_name in files:
                        if file_name.endswith(video_extensions):
                            file_keywords = split_keywords(file_name)
                            
                            matched_keywords = [kw for kw in entry_keywords if kw in file_keywords]
                            
                            print(f"Entry Name: {entry['name']}")
                            print(f"File Name: {file_name}")
                            print(f"Entry Keywords: {entry_keywords}")
                            print(f"File Keywords: {file_keywords}")
                            print(f"Matched Keywords: {matched_keywords}")
                            
                            # 70% of the keywords match, it a match
                            if len(matched_keywords) >= 0.5 * len(entry_keywords):
                                return os.path.join(root, file_name)
                            else:
                                print(f"Not enough keyword matches for {file_name}. Matched: {len(matched_keywords)} out of {len(entry_keywords)}")
                                print(f"No matching file found for torrent ID: {id}")
                                return None
        
                            
        return None