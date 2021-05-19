from . import EAGate, DDRRivalTableParser, DDRMusicPageParser


class DDRApi():

    def __init__(self, eagate):
        """
        Sets up an object to make DDR-specific API calls
        :param eagate: An authenticated EAGate object
        """
        self.eagate = eagate

    def fetch_recent_players(self):
        """
        Retrieves recent players from the arcade you were at last.
        :return: a DDRRival list of rivals
        :rtype: List[DDRRival]
        """
        uri = 'https://p.eagate.573.jp/game/ddr/ddra20/p/rival/kensaku.html?mode=4' # TODO, add maintence check.

        html = self.eagate.get_page(uri)

        rival_parser = DDRRivalTableParser.DDRRivalTableParser()
        rival_parser.feed(html)
        rivals = rival_parser.rivals

        return rivals

    def lookup_rival(self, rival_id):
        """
        Searches for a rival by ddr-id
        :param rival_id: ID of rival to lookup
        :return: Rival if found or none
        :rtype: DDRRivalTableParser.DDRRival
        """
        uri = 'https://p.eagate.573.jp/game/ddr/ddra20/p/rival/kensaku.html?mode=6&slot=&code=%i' % rival_id

        html = self.eagate.get_page(uri)

        rival_parser = DDRRivalTableParser.DDRRivalTableParser()
        rival_parser.feed(html)
        if len(rival_parser.rivals) == 0:
            return None
        else:
            return rival_parser.rivals[0]

    def lookup_rivals(self, search_query):
        """
        Searches for a user by name
        :param search_query: Name to search
        :return: List of rivals
        :rtype: List[DDRRivalTableParser.DDRRival]
        """
        uri = 'https://p.eagate.573.jp/game/ddr/ddra20/p/rival/kensaku.html?mode=1&name=%s&area=-1&slot=' % search_query
        html = self.eagate.get_page(uri)

        rival_parser = DDRRivalTableParser.DDRRivalTableParser()
        rival_parser.feed(html)

        return rival_parser.rivals

    def get_ddr_songs(self):
        uri_base = "https://p.eagate.573.jp/game/ddr/ddra20/p/music/index.html?offset=%i&filter=0&filtertype=0&playmode=2"
        offset = 0

        songs = []
        while offset < 20:
            html = self.eagate.get_page(uri_base % offset)
            parser = DDRMusicPageParser.DDRMusicPageParser(html)
            if len(parser.songs) == 0:
                break

            for song in parser.songs:
                songs.append(dict(song))

            offset += 1

        return songs
