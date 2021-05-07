import requests, json

from .Exceptions import EALinkException, EALoginException, EAMaintenanceException

base_url = "https://aqb-web.mo.konami.net/aqb/"
user_agent = "jp.konami.eam.link (Pixel 3 XL; Android 9; in-app; 20; app-version; 3.5.4.193)"
headers = {'User-Agent': user_agent}

# TODO
# * Move various json data structures into Python data classes


class EALink(object):

    def __init__(self, token=None, cookies=None):
        self.token = token
        self.cookies = cookies
        self.logged_in = False
        self.session = None
        self.my_uuid = None

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

    def get_my_uuid(self):
        if not self.logged_in:
            self.login()

        r = self.session.get("%s/user/checkSession.php" % base_url, headers=headers)

        js = json.loads(r.text)
        if js['status']:
            return js['user_info']['uuid']
        else:
            raise EALinkException("Error checking session!", jscontext=js)

    def get_jpeg_data_for(self, file_path):
        if not self.logged_in:
            self.login()

        r = self.session.get("%s/blog/post/webdav/detail.php?filepath=%s" % (base_url, file_path), headers=headers)
        if 'application/json' in r.headers['content-type']:
            raise EALinkException("Can't fetch screenshots, login failure?", jscontext=json.loads(r.content))
        elif r.headers['content-type'] != 'image/jpeg':
            raise Exception("Webdav file %s is not a JPEG! Got %s" % (file_path, r.headers['content-type']))

        return r.content

    def facility_index(self):
        if not self.logged_in:
            self.login()

        r = self.session.get("%s/blog/profile/facility/userFacilityIndex.php" % base_url, headers=headers)

    def user_search(self, nickname):
        if not self.logged_in:
            self.login()

        r = self.session.get("%s/blog/profile/search.php?nick_name=%s" % (base_url, nickname), headers=headers)

        js = json.loads(r.text)

        if not js['status']:
            raise EALinkException("Unable to search for users!", jscontext=js)

        return js['profile_list']

    def user_detail(self, uuid):
        if not self.logged_in:
            self.login()

        r = self.session.get("%s/blog/profile/inDetail.php?uuid_to=%s" % (base_url, uuid), headers=headers)

        return json.loads(r.text)['profile_info']

    def get_api_in_session(self, api):
        return self.get_in_session("%s/%s" % (base_url, api))

    def get_in_session(self, url):
        if not self.logged_in:
            self.login()

        r = self.session.get(url, headers=headers)

        return r.content