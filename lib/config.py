import os
from lib.pixiv import PixivAPI
from lib import utils

class Config:

    api = PixivAPI()

    def __init__(self, file_path):
        self.file_path = file_path
        self._data = utils.load_json(file_path)
        self._data["save_directory"] = os.path.normpath(self._data["save_directory"])
        self._data["artists"] = list(dict.fromkeys(self._data["artists"]))

    def print(self):
        utils.print_json(self._data)

    def update(self):
        utils.write_json(self._data, self.file_path)

    @property
    def username(self):
        return self._data["username"]

    @username.setter
    def username(self, username):
        self._data["username"] = username

    @property
    def password(self):
        return self._data["password"]

    @password.setter
    def password(self, password):
        self._data["password"] = password

    @property
    def save_dir(self):
        return self._data["save_directory"]

    @save_dir.setter
    def save_dir(self, save_dir):
        save_dir = os.path.normpath(save_dir)
        self._data["save_directory"] = save_dir

    @property
    def artists(self):
        return self._data["artists"]

    def add_artists(self, artist_ids):
        for id in artist_ids:
            if id not in self.artists:
                try:
                    self.api.artist(id)
                    self.artists.append(id)
                except:
                    print(f"Pixiv ID {id} does not exist")
            else:
                print(f"Pixiv ID {id} already exists in config file")

    def delete_artists(self, artist_ids):
        if "all" in artist_ids:
            artist_ids = self.artists.copy()
        for id in artist_ids:
            if id in self.artists:
                self.artists.remove(id)
                utils.remove_dir(self.save_dir, str(id))
            else:
                print(f"Pixiv ID {id} does not exist in config file")

    def clear_artists(self, artist_ids):
        if "all" in artist_ids:
            artist_ids = self.artists.copy()
        for id in artist_ids:
            if id in self.artists:
                utils.remove_dir(self.save_dir, str(id))
            else:
                print(f"Pixiv ID {id} does not exist in config file")