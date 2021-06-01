from bs4 import BeautifulSoup
from py573jp import EAGate, DDRPage
import os


# TODO Possibly track difficulties in here too...
class DDRSong:

    def __init__(self, song_title, artist):
        self.song_title = song_title
        self.artist = artist

    def __iter__(self):
        for key in ['song_title', 'artist']:
            yield key, getattr(self, key)

    def __str__(self):
        return "%s / %s" % (self.song_title, self.artist)


class DDRMusicPageParser:

    def __init__(self, html_text):
        self.html_text = html_text
        self.songs = []
        self.parse()

    def parse(self):
        soup = BeautifulSoup(self.html_text, 'html.parser')
        attrs = {
            'class': "data"
        }

        datas = soup.find_all('tr', attrs=attrs)

        for data_entry in datas:
            self.songs.append(DDRSong(data_entry.find('td', class_="music_tit").text,
                                      data_entry.find('td', class_="artist_nam").text))


def update_songdb():
    if not os.path.exists("DDRGenie/genie_assets/a20_songlist.json"):
        ddrapi = DDRPage.DDRApi(EAGate.EAGate())
        songs = ddrapi.get_ddr_songs()
        return songs


if __name__ == "__main__":
    import json
    song_list = update_songdb()
    new_songs = []
    for song in song_list:
        new_songs.append(song)
    print(json.dumps(new_songs))
