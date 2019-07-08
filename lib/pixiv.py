import multiprocessing
from multiprocessing.pool import ThreadPool
from functools import partial
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os, re, sys
from lib import utils

class PixivAPI:

    threads = multiprocessing.cpu_count() * 3
    chunk_size = 1048576

    def __init__(self):
        self.session = requests.Session()
        # retry when exceed the max request number
        retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
        self.session.mount("http://", HTTPAdapter(max_retries=retries))
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    def request(self, method, url, **kwargs):
        if method == "GET":
            res = self.session.get(url, **kwargs)
        elif method == "POST":
            res = self.session.post(url, **kwargs)
        res.raise_for_status()
        return res

    def login(self, username, password):
        url = "https://accounts.pixiv.net/login"
        res = self.request("GET", url)
        post_key = re.search(r"post_key\" value=\"(.*?)\">", res.text)[1]
        data = {
            "pixiv_id": username,
            "password": password,
            "post_key": post_key
        }
        self.request("POST", url, data=data)

    def user(self, user_id):
        res = self.request("GET", f"https://www.pixiv.net/ajax/user/{user_id}")
        return res.json()["body"]

    def artwork(self, artwork_id):
        res = self.request("GET", f"https://www.pixiv.net/ajax/illust/{artwork_id}")
        return res.json()["body"]

    def bookmarks(self, user_id):
        limit = 10000
        url = "https://www.pixiv.net/ajax/user/{}/illusts/bookmarks?tag=&offset=0&limit={}&rest=show"
        json = self.request("GET", url.format(user_id, limit)).json()["body"]
        if json["total"] > limit:
            json = self.request("GET", url.format(user_id, json["total"])).json()["body"]
        return json["works"]

    def rankings(self, mode, content, date, limit=None):
        """
        R18 contents require login()

        available modes for content "all": [daily, weekly, monthly, rookie, original, male, female, daily_r18, weekly_r18, male_r18, female_r18]
        available modes for content "illust": [daily, weekly, monthly, rookie, daily_r18, weekly_r18]
        available modes for content "ugoira": [daily, weekly, daily_r18, weekly_r18, male_r18, female_r18]
        available modes for content "manga": [daily, weekly, monthly, rookie, daily_r18, weekly_r18, male_r18, female_r18]
        """
        url = "https://www.pixiv.net/ranking.php?mode={}&content={}&date={}&p={}&format=json"
        json = self.request("GET", url.format(mode, content, date, 1)).json()
        items = json["contents"]
        limit = json["rank_total"] if limit is None else int(limit)
        for i in range(2, -(-limit // 50) + 1):
            json = self.request("GET", url.format(mode, content, date, i)).json()
            items.extend(json["contents"])
        return items[:limit]

    def user_artworks(self, user_id, dir_path=None):
        res = self.request("GET", f"https://www.pixiv.net/ajax/user/{user_id}/profile/all")
        json = res.json()["body"]
        artwork_ids = [*json["illusts"], *json["manga"]]
        # sort ids in descending order, i.e. newest to oldest
        artwork_ids.sort(key=int, reverse=True)
        limit = None
        if dir_path and utils.file_names(dir_path):
            file_names = utils.file_names(dir_path, separator="_")
            limit = utils.first_index(artwork_ids, lambda id: id in file_names)
        with ThreadPool(self.threads) as pool:
            artworks = pool.map(self.artwork, artwork_ids[:limit])
        return artworks

    def user_bookmarks_artworks(self, user_id, dir_path=None):
        artwork_ids = [a["id"] for a in self.bookmarks(user_id)]
        limit = None
        if dir_path and utils.file_names(dir_path):
            file_names = utils.file_names(dir_path, separator="_")
            limit = utils.first_index(artwork_ids, lambda id: id in file_names)
        with ThreadPool(self.threads) as pool:
            artworks = pool.map(self.artwork, artwork_ids[:limit])
        return artworks

    def rankings_artworks(self, mode, content, date, limit, dir_path=None):
        artwork_ids = [str(a["illust_id"]) for a in self.rankings(mode, content, date, limit)]
        if dir_path and utils.file_names(dir_path):
            file_names = utils.file_names(dir_path, separator="_")
            artwork_ids = [a for a in artwork_ids if a not in file_names]
        with ThreadPool(self.threads) as pool:
            artworks = pool.map(self.artwork, artwork_ids)
        return artworks

    def download_url(self, count, artwork):
        # illustType: 0 = normal image, 1 = manga, 2 = ugoira
        if artwork["illustType"] == 0 or artwork["illustType"] == 1:
            url = artwork["urls"]["original"]
            return re.sub("p0", f"p{count}", url)
        elif artwork["illustType"] == 2:
            res = self.request("GET", f"https://www.pixiv.net/ajax/illust/{artwork['id']}/ugoira_meta")
            return res.json()["body"]["originalSrc"]

    def save_artwork(self, dir_path, artwork):
        file = {
            "id": [artwork["id"]],
            "title": [artwork["title"]],
            "urls": [],
            "names": [],
            "count": artwork["pageCount"],
            "size": 0
        }
        for i in range(artwork["pageCount"]):
            url = self.download_url(i, artwork)
            file["urls"].append(url)
            headers = {"referer": f"https://www.pixiv.net/member_illust.php?mode=medium&illust_id={artwork['id']}"}
            res = self.request("GET", url, headers=headers, stream=True)
            file_name = re.search(r"\d+_(p|ugoira).*?\..*", url)[0]
            file["names"].append(file_name)
            with open(os.path.join(dir_path, file_name), "wb") as f:
                for chunk in res.iter_content(chunk_size=self.chunk_size):
                    f.write(chunk)
                    file["size"] += len(chunk)
            print(f"download image: {artwork['title']} ({file_name})")
        return file

    def save_artworks(self, user_id, dir_path):
        username = self.user(user_id)["name"]
        print(f"download artworks for user {username}\n")
        dir_path = utils.make_dir(dir_path, str(user_id))
        artworks = self.user_artworks(user_id, dir_path)
        if not artworks:
            print(f"user {username} is up-to-date\n")
            return
        with ThreadPool(self.threads) as pool:
            files = pool.map(partial(self.save_artwork, dir_path), artworks)
        print(f"\ndownload for user {username} completed\n")
        combined_files = utils.dict_counter(files)
        utils.set_files_mtime(combined_files["names"], dir_path)
        return combined_files

    def save_bookmarks(self, user_id, dir_path):
        username = self.user(user_id)["name"]
        print(f"download bookmarks for user {username}\n")
        dir_path = utils.make_dir(dir_path, str(user_id) + " bookmarks")
        artworks = self.user_bookmarks_artworks(user_id, dir_path)
        if not artworks:
            print(f"user {username} is up-to-date\n")
            return
        with ThreadPool(self.threads) as pool:
            files = pool.map(partial(self.save_artwork, dir_path), artworks)
        print(f"\ndownload for user {username} completed\n")
        combined_files = utils.dict_counter(files)
        utils.set_files_mtime(combined_files["names"], dir_path)
        return combined_files

    def save_rankings(self, mode, content, date, limit, dir_path):
        print(f"download {mode} {content} rankings\n")
        dir_path = utils.make_dir(dir_path, f"{mode} {content} rankings")
        artworks = self.rankings_artworks(mode, content, date, limit, dir_path)
        if not artworks:
            print(f"{mode} {content} rankings are up-to-date\n")
            return
        with ThreadPool(self.threads) as pool:
            files = pool.map(partial(self.save_artwork, dir_path), artworks)
        print(f"\ndownload for {mode} {content} rankings completed\n")
        combined_files = utils.dict_counter(files)
        utils.set_files_mtime(combined_files["names"], dir_path)
        return combined_files

    def save_users_artworks(self, user_ids, dir_path):
        print(f"\nthere are {len(user_ids)} users\n")
        result = []
        for user in user_ids:
            files = self.save_artworks(user, dir_path)
            if not files:
                continue
            result.append(files)
        return utils.dict_counter(result)

    def save_users_bookmarks(self, user_ids, dir_path):
        print(f"\nthere are {len(user_ids)} users\n")
        result = []
        for user in user_ids:
            files = self.save_bookmarks(user, dir_path)
            if not files:
                continue
            result.append(files)
        return utils.dict_counter(result)

    # TODO - incomplete, see issue for potential implementation
    def recommend(self, user_ids):
        import collections
        counter = collections.Counter()
        for id in user_ids:
            counter += collections.Counter([a["userId"] for a in self.bookmarks(id)])
        return counter.most_common()