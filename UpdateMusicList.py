import os
from py573jp import DDRPage, EAGate

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
