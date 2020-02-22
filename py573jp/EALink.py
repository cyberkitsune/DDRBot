import requests, json

from .Exceptions import EALinkException, EALoginException, EAMaintenanceException

base_url = "https://aqb.s.konaminet.jp/aqb/"
user_agent = "jp.konami.eam.link (Pixel2; Android 9.0; in-app; 20; app-version; 3.5.0)"
headers = {'User-Agent': user_agent}


class EALink(object):
    session = None
    token = None
    logged_in = False
    cookies = None

    def __init__(self, token=None, cookies=None):
        self.token = token
        self.cookies = cookies

    def login(self, username=None, password=None, otp=None):
        if self.session is not None:
            return
        self.session = requests.session()
        if self.cookies is not None:
            if len(self.cookies) < 2:
                raise Exception("EALink cookie jar too small!")
            self.session.cookies['_ga'] = self.cookies[0]
            self.session.cookies['aqblog'] = self.cookies[1]
            return
        if self.token is not None:
            data = {'method': "login_token", 'login_token': self.token, 'format': "json"}
            r = self.session.post("%s/user/login.php" % base_url, data=data, headers=headers)
            js = json.loads(r.text)
            if js['status']:
                self.token = js['login_token']
                self.logged_in = True
                self.cookies = (self.session.cookies['aqbsess'], self.session.cookies['aqblog'])
                return self.token
            else:
                raise EALinkException("Unable to log in!", js)
        else:
            data = {'username': username, 'password': password, 'otp_password': otp, 'format': "json"}
            r = self.session.post("%s/user/login.php" % base_url, data=data, headers=headers)
            js = json.loads(r.text)
            if js['status']:
                self.token = js['login_token']
                self.logged_in = True
                self.cookies = (self.session.cookies['aqbsess'], self.session.cookies['aqblog'])
                return self.token
            else:
                raise EALinkException("Unable to log in! Check your username / password / OTP. Server: %s" % js['message'], js)

    def get_screenshot_list(self):
        if not self.logged_in:
            self.login()

        r = self.session.get("%s/blog/post/webdav/index.php" % base_url, headers=headers)
        photos = []
        js = json.loads(r.text)
        if js is None:
            raise EALinkException("Can't parse response! Server Issues?", r.text)
        if 'list' not in js:
            raise EALoginException("Unable to fetch photos! Maybe you've been logged out?", js)
        if js['list'] is None:
            raise EAMaintenanceException("Screenshot list is NULL! This usually indicates e-amusement maintenance. Try again later.")
        for photo in js['list']:
            photos.append(photo)

        return photos

    def get_jpeg_data_for(self, file_path):
        if not self.logged_in:
            self.login()

        r = self.session.get("%s/blog/post/webdav/detail.php?filepath=%s" % (base_url, file_path), headers=headers)
        if r.headers['content-type'] == 'application/json':
            raise Exception("Webdav file %s is not a JPEG! I got json...\nOutput: %s" % (file_path, r.content))
        elif r.headers['content-type'] != 'image/jpeg':
            raise Exception("Webdav file %s is not a JPEG! Got %s" % (file_path, r.headers['content-type']))

        return r.content
