from multiprocessing.pool import ThreadPool
from functools import partial
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from argparse import ArgumentParser
import time
import re
import json
import os


USER_FILE = "info.json"
THREADS = 24
MB_BYTES = 1048576
image_num = 0
total_size = 0


def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(data, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def request(session, method, url, response="", headers={}, data={}, stream=False):
    if method == "GET":
        res = session.get(url, headers=headers, stream=stream)
    elif method == "POST":
        res = session.post(url, headers=headers, data=data)
    # check if request is successful
    res.raise_for_status()
    
    if response == "HTML": return res.text
    elif response == "BINARY": return res.content
    elif response == "JSON": return res.json()
    else: return res



def create_directory(save_directory, artist_name=""):
    dir_path = os.path.join(save_directory, artist_name)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path


def login(session, username, password):
    login_url = "https://accounts.pixiv.net/login?lang=en&source=pc&view_type=page&ref=wwwtop_accounts_index"
    html = request(session, "GET", login_url, "HTML")
    post_key = re.search(r"post_key\" value=\"(.*?)\">", html)[1]
    data = {
        "pixiv_id": username,
        "password": password,
        "post_key": post_key
    }
    request(session, "POST", login_url, data=data)


def get_artist_name(session, artist_id):
    json = request(session, "GET", f"https://www.pixiv.net/ajax/user/{artist_id}", "JSON")
    return json["body"]["name"]


def get_artwork(session, artwork_id):
    json = request(session, "GET", f"https://www.pixiv.net/ajax/illust/{artwork_id}", "JSON")
    return json["body"]


def get_artworks(session, user_info, artist_id):
    json = request(session, "GET", f"https://www.pixiv.net/ajax/user/{artist_id}/profile/all", "JSON")
    artist_profile = json["body"]
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
        artworks = pool.map(partial(get_artwork, session), artwork_ids[:index])
    return artworks


def get_download_url(session, count, artwork):
    # illustType: 0 = normal image, 1 = manga, 2 = ugoira
    if artwork["illustType"] == 0 or artwork["illustType"] == 1:
        url = artwork["urls"]["original"]
        return re.sub("p0", f"p{count}", url)
    elif artwork["illustType"] == 2:
        json = request(session, "GET", f"https://www.pixiv.net/ajax/illust/{artwork['id']}/ugoira_meta", "JSON")
        return json["body"]["originalSrc"]


def save_artwork(session, dir_path, artwork):
    file_names = []
    for count in range(artwork["pageCount"]):
        url = get_download_url(session, count, artwork)
        headers = { "referer": f"https://www.pixiv.net/member_illust.php?mode=medium&illust_id={artwork['id']}" }
        res = request(session, "GET", url, headers=headers, stream=True)
        file_name = re.search(r"\d+_(p|ugoira).*?\..*", url)[0]
        file_names.append(file_name)
        with open(os.path.join(dir_path, file_name), "wb") as f:
            for chunk in res.iter_content(chunk_size=MB_BYTES):
                f.write(chunk)
                global total_size
                total_size += len(chunk)
            global image_num
            image_num += 1
        print(f"download image: {artwork['title']} ({file_name})")
    return file_names


# change file modification dates to allow sorting in File Explorer
def modify_files_dates(file_names, dir_path):
    current_time = time.time()
    # from oldest to newest
    file_names.reverse()
    for file_name in file_names:
        file_path = os.path.join(dir_path, file_name)
        os.utime(file_path, (current_time, current_time))
        current_time += 1


def download_artist(session, user_info, artist_id):
    artist_name = get_artist_name(session, artist_id)
    print(f"download for artist {artist_name} begins\n")
    artworks = get_artworks(session, user_info, artist_id)
    if not artworks:
        print(f"author {artist_name} is up-to-date\n")
        return
    dir_path = create_directory(user_info["save_directory"], artist_name)
    with ThreadPool(THREADS) as pool:
        file_names = pool.map(partial(save_artwork, session, dir_path), artworks)
    print(f"\ndownload for artist {artist_name} completed\n")

    # convert lists of list to flat list
    file_names = [item for sublist in file_names for item in sublist]
    modify_files_dates(file_names, dir_path)


def download_artists(session):
    user_info = read_json(USER_FILE)
    print("\nLogging in to Pixiv")
    login(session, user_info["username"], user_info["password"])

    start_time = time.time()
    print(f"\nthere are {len(user_info['artist_ids'])} artists...\n")
    create_directory(user_info["save_directory"])
    for id in user_info["artist_ids"]:
        download_artist(session, user_info, id)
    write_json(user_info, USER_FILE)

    duration = time.time() - start_time
    size_mb = total_size / MB_BYTES
    print("\nSUMMARY")
    print("---------------------------------")
    print(f"time elapsed:\t{duration:.4f} seconds")
    print(f"total size:\t{size_mb:.4f} MB")
    print(f"total artworks:\t{image_num} artworks")
    print(f"download speed:\t{(size_mb / duration):.4f} MB/s")


def set_key_value(key, value):
    user_info = read_json(USER_FILE)
    user_info[key] = value
    write_json(user_info, USER_FILE)


def add_artists(session, artist_ids):
    user_info = read_json(USER_FILE)
    for artist_id in artist_ids:
        try:
            get_artist_name(session, artist_id)
            if artist_id not in user_info["artist_ids"]:
                user_info["artist_ids"].append(artist_id)
                write_json(user_info, USER_FILE)
            else: print(f"artist ID {artist_id} already exists")
        except requests.exceptions.HTTPError:
            print(f"artist has left pixiv or the artist ID {artist_id} does not exist")
            pass


def delete_artists(artist_ids):
    user_info = read_json(USER_FILE)
    for artist_id in artist_ids:
        try:
            user_info["artist_ids"].remove(artist_id)
        except ValueError:
            pass
        user_info["update_info"].pop(artist_id, None)
    write_json(user_info, USER_FILE)


def main():
    session = requests.Session()
    # retry when exceed the max request number
    retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))

    # CLI
    parser = ArgumentParser()
    parser.add_argument("-u", dest="username", help="set pixiv username")
    parser.add_argument("-p", dest="password", help="set pixiv password")
    parser.add_argument("-s", dest="save_dir", help="set save directory")
    parser.add_argument("-a", nargs="+", dest="add", help="add artist ids", metavar="")
    parser.add_argument("-d", nargs="+", dest="delete", help="delete artist ids", metavar="")
    parser.add_argument("-r", action="store_true", dest="run", help="run program")
    args = parser.parse_args()

    if args.username: set_key_value("username", args.username)
    if args.password: set_key_value("password", args.password)
    if args.save_dir: set_key_value("save_directory", args.save_dir)
    if args.add: add_artists(session, args.add)
    if args.delete: delete_artists(args.delete)
    if args.run: download_artists(session)


if __name__ == "__main__":
    main()