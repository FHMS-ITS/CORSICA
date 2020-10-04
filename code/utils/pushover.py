import json
import requests


class Pushover:
    def __init__(self, app_token, user_key, message):
        self.data = {"token": app_token, "user": user_key, "message": message}
        self.key_list = ['token', 'user', 'title', 'message', 'url', 'url_title', 'device', 'priority', 'timestamp',
                         'expire', 'retry', 'callback', 'sound']

    def send(self):
        c = requests.post("https://api.pushover.net:443/1/messages.json", data=self.data,
                          headers={"Content-type": "application/x-www-form-urlencoded"})
        return json.loads(c.text)

    def set_data(self, key, value):
        if key in self.key_list:
            self.data[key] = value
        else:
            self.__print_error(key)

    def get_data(self, key):
        return self.data[key]

    def get_possible_keys(self):
        return self.key_list

    def __print_error(self, key):
        print("ERROR: Invalid Key %s. Possible keys: %s" % (key, self.key_list))
        raise KeyError(key)
