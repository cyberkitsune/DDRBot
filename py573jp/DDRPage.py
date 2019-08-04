from . import EAGate, DDRRivalTableParser


class DDRApi():
    eagate: EAGate = None

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

        :param rival_id:
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
