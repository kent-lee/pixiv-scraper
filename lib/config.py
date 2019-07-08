import os
from lib.pixiv import PixivAPI
from lib import utils

class Config:

    api = PixivAPI()

    def __init__(self, file_path):
        self.file_path = file_path
        self._data = utils.load_json(file_path)
        self._data["save_directory"] = os.path.normpath(self._data["save_directory"])
        self._data["users"] = list(dict.fromkeys(self._data["users"]))
        self._data["bookmarks"] = list(dict.fromkeys(self._data["bookmarks"]))

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
    def users(self):
        return self._data["users"]

    @property
    def bookmarks(self):
        return self._data["bookmarks"]

    def add_users(self, user_ids):
        for id in user_ids:
            if id not in self.users:
                try:
                    self.api.user(id)
                    self.users.append(id)
                except:
                    print(f"Pixiv ID {id} does not exist")
            else:
                print(f"Pixiv ID {id} already exists in config file")

    def delete_users(self, user_ids):
        if "all" in user_ids:
            user_ids = self.users.copy()
        user_ids = [int(id) for id in user_ids]
        for id in user_ids:
            if id in self.users:
                self.users.remove(id)
                utils.remove_dir(self.save_dir, str(id))
            else:
                print(f"Pixiv ID {id} does not exist in config file")

    def clear_users(self, user_ids):
        if "all" in user_ids:
            user_ids = self.users.copy()
        user_ids = [int(id) for id in user_ids]
        for id in user_ids:
            if id in self.users:
                utils.remove_dir(self.save_dir, str(id))
            else:
                print(f"Pixiv ID {id} does not exist in config file")

    def add_bookmarks(self, user_ids):
        for id in user_ids:
            if id not in self.bookmarks:
                try:
                    self.api.user(id)
                    self.bookmarks.append(id)
                except:
                    print(f"Pixiv ID {id} does not exist")
            else:
                print(f"Pixiv ID {id} already exists in config file")

    def delete_bookmarks(self, user_ids):
        if "all" in user_ids:
            user_ids = self.bookmarks.copy()
        user_ids = [int(id) for id in user_ids]
        for id in user_ids:
            if id in self.bookmarks:
                self.bookmarks.remove(id)
                utils.remove_dir(self.save_dir, str(id) + " bookmarks")
            else:
                print(f"Pixiv ID {id} does not exist in config file")

    def clear_bookmarks(self, user_ids):
        if "all" in user_ids:
            user_ids = self.bookmarks.copy()
        user_ids = [int(id) for id in user_ids]
        for id in user_ids:
            if id in self.bookmarks:
                utils.remove_dir(self.save_dir, str(id) + " bookmarks")
            else:
                print(f"Pixiv ID {id} does not exist in config file")

    # def delete_rankings(self, **kwargs):
    #     file_path = 
    #     for id in user_ids:
    #         if id in self.bookmarks:
    #             self.bookmarks.remove(id)
    #             utils.remove_dir(self.save_dir, str(id) + " bookmarks")
    #         else:
    #             print(f"Pixiv ID {id} does not exist in config file")

    # def clear_rankings(self, user_ids):
    #     if "all" in user_ids:
    #         user_ids = self.bookmarks.copy()
    #     user_ids = [int(id) for id in user_ids]
    #     for id in user_ids:
    #         if id in self.bookmarks:
    #             utils.remove_dir(self.save_dir, str(id) + " bookmarks")
    #         else:
    #             print(f"Pixiv ID {id} does not exist in config file")