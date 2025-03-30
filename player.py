import vlc
import threading
import time

class Player:
    def __init__(self):
        self.media_path = None
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

    def set_media(self, media_path):
        self.media_path = media_path
        media = self.instance.media_new(media_path)
        self.player.set_media(media)

    def play(self):
        if not self.media_path:
            print("No media file set!")
            return
        self.player.set_fullscreen(True)
        self.player.play()
        return True

    def pause(self):
        if self.player.is_playing():
            self.player.pause()
        else:
            self.player.play()

    def fast_forward(self, seconds=10):
        current_time = self.player.get_time()
        self.player.set_time(current_time + (seconds * 1000))

    def rewind(self, seconds=10):
        current_time = self.player.get_time()
        new_time = max(0, current_time - (seconds * 1000))
        self.player.set_time(new_time)

    def enable_subtitles(self):
        self.player.video_set_spu(0)  # 0 is usually the first subtitle track

    def disable_subtitles(self):
        self.player.video_set_spu(-1)  # -1 disables subtitles

    def stop_and_close(self):
        self.player.stop()

    def is_playing(self):
        return self.player.is_playing()

if __name__ == "__main__":
    player = Player()
    player.set_media("example.mp4")
    player.play()
    time.sleep(5)  # Let it play for 5 seconds
    player.fast_forward(10)  # Fast forward 10 seconds
    time.sleep(5)
    player.pause()
    time.sleep(2)
    player.play()
    time.sleep(5)
    player.stop_and_close()
