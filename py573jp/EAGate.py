import requests

class EAGate():
    logged_in = False
    session_id = None


    def __init__(self, session_id=None):
        """
        E-Amusment API Object. Use this for e-amusement related operations
        :param session_id: Specify a session ID, if you have one
        """
        if session_id is not None:
            self.session_id = session_id

    def login(self, username, password, otp=None):
        """
        Logs you into e-amusement and sets the session ID for the API.
        This is not yet implemented, as I need to figure out how to handle the capcha
        :param username: E-Amusement username
        :param password: E-Amusement password
        :param otp: One-time-password, if enabled on the account
        :return:
        """
        pass

    def get_page(self, uri):
        if self.session_id is None:
            raise Exception("EAGate API is not authenticated! Please login or specify a session id.")
        cookies = dict(M573SSID=self.session_id)
        r = requests.get(uri, cookies=cookies)
        r.raise_for_status() # Error handling for 404, 403, etc...

        return r.text
