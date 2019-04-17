from multiprocessing.pool import ThreadPool
from functools import partial
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os, re, utils, stats


def init_session():
    session = requests.Session()
    # retry when exceed the max request number
    retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


def request(session, method, url, headers={}, data={}, stream=False):
    if method == "GET":
        res = session.get(url, headers=headers, stream=stream)
    elif method == "POST":
        res = session.post(url, headers=headers, data=data)
    # raise requests.exception.HTTPError if request is not 200
    res.raise_for_status()
    return res


def login(session, username, password):
    login_url = "https://accounts.pixiv.net/login?lang=en&source=pc&view_type=page&ref=wwwtop_accounts_index"
    res = request(session, "GET", login_url)
    post_key = re.search(r"post_key\" value=\"(.*?)\">", res.text)[1]
    data = {
        "pixiv_id": username,
        "password": password,
        "post_key": post_key
    }
    request(session, "POST", login_url, data=data)


def artist_name(session, id):
    try:
        res = request(session, "GET", f"https://www.pixiv.net/ajax/user/{id}")
        return res.json()["body"]["name"]
    except requests.exceptions.HTTPError:
        print(f"artist ID {id} has left Pixiv or the artist does not exist")
        return None


def artwork(session, id):
    res = request(session, "GET", f"https://www.pixiv.net/ajax/illust/{id}")
    return res.json()["body"]


def artworks(session, user, id):
    res = request(session, "GET", f"https://www.pixiv.net/ajax/user/{id}/profile/all")
    artist = res.json()["body"]
    artwork_ids = [*artist["illusts"], *artist["manga"]]
    # sort ids in descending order, i.e. newest to oldest
    artwork_ids.sort(key=int, reverse=True)
    # find index of first matched
    last_visit = next((i for i,v in enumerate(artwork_ids) if v == user["artists"][id]), len(artwork_ids))
    with ThreadPool(user["threads"]) as pool:
        works = pool.map(partial(artwork, session), artwork_ids[:last_visit])
    user["artists"][id] = artwork_ids[0]
    return works


def get_download_url(session, count, artwork):
    # illustType: 0 = normal image, 1 = manga, 2 = ugoira
    if artwork["illustType"] == 0 or artwork["illustType"] == 1:
        url = artwork["urls"]["original"]
        return re.sub("p0", f"p{count}", url)
    elif artwork["illustType"] == 2:
        res = request(session, "GET", f"https://www.pixiv.net/ajax/illust/{artwork['id']}/ugoira_meta")
        return res.json()["body"]["originalSrc"]


def download_artwork(session, dir_path, artwork):
    files = []
    for i in range(artwork["pageCount"]):
        url = get_download_url(session, i, artwork)
        headers = {"referer": f"https://www.pixiv.net/member_illust.php?mode=medium&illust_id={artwork['id']}"}
        res = request(session, "GET", url, headers=headers, stream=True)
        file_name = re.search(r"\d+_(p|ugoira).*?\..*", url)[0]
        files.append(file_name)
        with open(os.path.join(dir_path, file_name), "wb") as f:
            for chunk in res.iter_content(chunk_size=1048576):
                f.write(chunk)
                stats.update_size(len(chunk))
        stats.update_files()
        print(f"download image: {artwork['title']} ({file_name})")
    return files


def download_artist(session, user, id):
    name = artist_name(session, id)
    print(f"download for artist {name} begins\n")
    works = artworks(session, user, id)
    if not works:
        print(f"author {name} is up-to-date\n")
        return
    dir_path = utils.mkdir(os.path.join(user["save_directory"], name))
    with ThreadPool(user["threads"]) as pool:
        files = pool.map(partial(download_artwork, session, dir_path), works)
    print(f"\ndownload for artist {name} completed\n")
    utils.set_modified_times(utils.flatten(files), dir_path)


def download_artists(session, user):
    stats.init_stats()
    print("\nlogging in to Pixiv...")
    login(session, user["username"], user["password"])
    print(f"\nthere are {len(user['artists'])} artists\n")
    utils.mkdir(user["save_directory"])
    for id in user["artists"].keys():
        download_artist(session, user, id)
    stats.display_stats()