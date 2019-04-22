import multiprocessing
from multiprocessing.pool import ThreadPool
from functools import partial
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os, re

class PixivAPI:

    threads = multiprocessing.cpu_count() * 4
    download_chunk_size = 1048576

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

    def artist(self, artist_id):
        res = self.request("GET", f"https://www.pixiv.net/ajax/user/{artist_id}")
        return res.json()["body"]
    
    def artwork(self, artwork_id):
        res = self.request("GET", f"https://www.pixiv.net/ajax/illust/{artwork_id}")
        return res.json()["body"]

    def artist_artworks(self, artist_id, start=1, stop=None):
        res = self.request("GET", f"https://www.pixiv.net/ajax/user/{artist_id}/profile/all")
        json = res.json()["body"]
        artwork_ids = [*json["illusts"], *json["manga"]]
        # sort ids in descending order, i.e. newest to oldest'
        artwork_ids.sort(key=int, reverse=True)
        start = artwork_ids.index(start) if isinstance(start, str) else start - 1
        stop = artwork_ids.index(stop) if isinstance(stop, str) else stop
        with ThreadPool(self.threads) as pool:
            artworks = pool.map(self.artwork, artwork_ids[start:stop])
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
        file_info = {
            "artwork_id": artwork["id"],
            "artwork_title": artwork["title"],
            "artwork_urls": [],
            "names": [],
            "count": artwork["pageCount"],
            "size": 0
        }
        for i in range(artwork["pageCount"]):
            url = self.download_url(i, artwork)
            file_info["artwork_urls"].append(url)
            headers = {"referer": f"https://www.pixiv.net/member_illust.php?mode=medium&illust_id={artwork['id']}"}
            res = self.request("GET", url, headers=headers, stream=True)
            file_name = re.search(r"\d+_(p|ugoira).*?\..*", url)[0]
            file_info["names"].append(file_name)
            with open(os.path.join(dir_path, file_name), "wb") as f:
                for chunk in res.iter_content(chunk_size=self.download_chunk_size):
                    f.write(chunk)
                    file_info["size"] += len(chunk)
            print(f"download image: {artwork['title']} ({file_name})")
        return file_info

    def save_artist(self, artist_id, dir_path, start=1, stop=None):
        artist_name = self.artist(artist_id)["name"]
        print(f"download for artist {artist_name} begins\n")
        artworks = self.artist_artworks(artist_id, start, stop)
        if not artworks:
            print(f"artist {artist_name} is up-to-date\n")
            return
        with ThreadPool(self.threads) as pool:
            files = pool.map(partial(self.save_artwork, dir_path), artworks)
        print(f"\ndownload for artist {artist_name} completed\n")
        return files