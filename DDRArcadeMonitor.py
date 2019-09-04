class DDRArcadeMonitor():
    api_key = None
    recent_players = []
    last_check = None

    def __init__(self, api_key):
        self.api_key = api_key
        self.recent_players = []
        self.last_check = None