from html.parser import HTMLParser


class DDRRival(object):
    name = None
    ddrid = 0
    position = 0

    def __init__(self, position):
        self.position = position

    def __str__(self):
        return "%i: %s [DDR-CODE %i]" % (self.position, self.name, self.ddrid)

    def __eq__(self, other):
        return self.ddrid == other.ddrid

    def __ne__(self, other):
        return self.ddrid != other.ddrid


class DDRRivalTableParser(HTMLParser):

    def __init__(self):
        self.currentTag = None
        self.currentPosition = 0
        self.currentClass = None
        self.currentRival = None
        self.rivals = []
        super().__init__()

    def handle_starttag(self, tag, attrs):
        self.currentTag = tag
        if tag == "td":
            if len(attrs) > 0 and attrs[0][0] == 'class' and any(x in attrs[0][1] for x in ['dancer_name', 'code']):
                self.currentClass = attrs[0][1]

    def handle_endtag(self, tag):
        self.currentTag = None
        if self.currentClass == 'code':
            self.currentPosition = self.currentPosition + 1
            self.currentClass = None
            self.rivals.append(self.currentRival)
            self.currentRival = None

    def handle_data(self, data):
        if self.currentClass is not None:
            if self.currentRival is None:
                self.currentRival = DDRRival(self.currentPosition)

            if self.currentClass == 'dancer_name':
                self.currentRival.name = data

            if self.currentClass == 'code':
                self.currentRival.ddrid = int(data)

    def error(self, message):
        raise Exception("Error parsing HTML: %s" % message)
