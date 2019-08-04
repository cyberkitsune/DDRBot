import requests

class EAGate():
    logged_in = False
    session_id = None

    def __init__(self, session_id=None):
        if session_id is not None:
            self.session_id = session_id

    def login(self, username, password, otp=None):
        pass