from html.parser import HTMLParser

class DDRRival(object):
    name = None
    ddrid = 0
    position = 0

    def __init__(self, position):
        self.position = position

class DDRRivalTableParser(HTMLParser):

    currentTag = None
    currentPosition = 0
    currentClass = None
    currentRival = None
    rivals = []

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
                self.currentRival.ddrid = data
