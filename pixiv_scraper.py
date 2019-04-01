from multiprocessing.pool import ThreadPool
from functools import partial
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import timeit
import re
import json


USER_FILE = "info.json"
THREADS = 24
image_num = 0
total_size = 0


def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(user_info, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(user_info, f, indent=4, ensure_ascii=False)


def create_directory(download_location, artist_name):
    dir_path = Path(download_location, artist_name)
    dir_path.mkdir(exist_ok=True)
    return dir_path


def login(session, username, password):
    login_url = "https://accounts.pixiv.net/login?lang=en&source=pc&view_type=page&ref=wwwtop_accounts_index"
    res = session.get(login_url)
    post_key = re.search(r"post_key\" value=\"(.*?)\">", res.text)[1]
    data = {
        "pixiv_id": username,
        "password": password,
        "post_key": post_key
    }
    session.post(login_url, data=data)


def get_artist_name(session, artist_id):
    res = session.get(f"https://www.pixiv.net/ajax/user/{artist_id}")
    if res.status_code == 404:
        print(f"{res.json()['message']}")
        return None
    return res.json()["body"]["name"]


def parse_json(session, artwork_id):
    url = f"https://www.pixiv.net/ajax/illust/{artwork_id}"
    res = session.get(url)
    return res.json()["body"]


def get_artworks(session, user_info, artist_id, offset=48):
    res = session.get(f"https://www.pixiv.net/ajax/user/{artist_id}/profile/all")
    artist_profile = res.json()["body"]
    artwork_ids = [*artist_profile["illusts"], *artist_profile["manga"]]
    # sort ids to check update
    artwork_ids.sort(key=int, reverse=True)
    if artist_id in user_info["update_info"]:
        last_visit_artwork = user_info["update_info"][artist_id]
    else:
        last_visit_artwork = ""
    user_info["update_info"][artist_id] = artwork_ids[0]

    # find index of first matched id
    index = next((i for i,artwork in enumerate(artwork_ids) if artwork == last_visit_artwork), len(artwork_ids))
    with ThreadPool(THREADS) as pool:
        artworks = pool.map(partial(parse_json, session), artwork_ids[:index])
    return artworks


def get_download_url(session, count, artwork):
    # illustType: 0 = normal image, 1 = manga, 2 = ugoira
    if artwork["illustType"] == 0 or artwork["illustType"] == 1:
        url = artwork["urls"]["original"]
        return re.sub("p0", f"p{count}", url)
    elif artwork["illustType"] == 2:
        res = session.get(f"https://www.pixiv.net/ajax/illust/{artwork['id']}/ugoira_meta")
        return res.json()["body"]["originalSrc"]


def save_artwork(session, dir_path, artwork):
    for count in range(artwork["pageCount"]):
        url = get_download_url(session, count, artwork)
        headers = { "referer": f"https://www.pixiv.net/member_illust.php?mode=medium&illust_id={artwork['id']}" }
        res = session.get(url, headers=headers)
        file_name = re.search(r"\d+_(p|ugoira).*?\..*", url)[0]
        file_size = (dir_path / file_name).write_bytes(res.content)
        print(f"download image: {artwork['title']} ({file_name})")
        global image_num, total_size
        image_num += 1
        total_size += file_size


def download_artist(session, user_info, artist_id):
    artist_name = get_artist_name(session, artist_id)
    if not artist_name:
        return
    print(f"download for artist {artist_name} begins\n")
    artworks = get_artworks(session, user_info, artist_id)
    if not artworks:
        print(f"author {artist_name} is up-to-date\n")
        return
    dir_path = create_directory(user_info["download_location"], artist_name)
    with ThreadPool(THREADS) as pool:
        pool.map(partial(save_artwork, session, dir_path), artworks)
    print(f"\ndownload for artist {artist_name} completed\n")


def main():
    start_time = timeit.default_timer()

    user_info = read_json(USER_FILE)
    session = requests.Session()
    # retry when exceed the max request number
    retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))
    login(session, user_info["username"], user_info["password"])
    
    print(f"\nthere are {len(user_info['artist_ids'])} artists...\n")
    for id in user_info["artist_ids"]:
        download_artist(session, user_info, id)
    write_json(user_info, USER_FILE)

    duration = timeit.default_timer() - start_time
    size_mb = total_size / 1048576
    print("\nSUMMARY")
    print("---------------------------------")
    print(f"time elapsed:\t{duration:.4f} seconds")
    print(f"total size:\t{size_mb:.4f} MB")
    print(f"total artworks:\t{image_num} artworks")
    print(f"download speed:\t{(size_mb / duration):.4f} MB/s")


if __name__ == "__main__":
    main()