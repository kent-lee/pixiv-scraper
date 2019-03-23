from multiprocessing.pool import ThreadPool
from functools import partial
from pixivpy3 import PixivAPI
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import timeit
import os
import re
import json


USER_FILE = "info.json"
THREADS = 24
image_num = 0
total_size = 0


# get user info from json file
def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# update user info to json file
def update_json(user_info, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(user_info, f, indent=4, ensure_ascii=False)


# create directory and name it using author name
def create_directory(author_name, download_location):
    dir_path = download_location + "\\" + author_name
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path


# get author name from an author id
def get_author_name(api, author_id):
    json = api.users(author_id)
    if None in json.response:
        return None
    return json.response[0].name


# get download url from image json object
def get_download_url(count, image):
    try:
        return re.sub("_p0", "_p"+str(count), image.image_urls.large)
    except re.error:
        return re.sub("_ugoira0", "_ugoira"+str(count), image.image_urls.large)


# flag update and return image objects up to last_visit_image in found_images
def check_update(found_images, last_visit_image):
    # find index of first matched element
    index = next((i for i, image in enumerate(found_images) if image.id == last_visit_image), None)
    if (not found_images) or (index is not None):
        return found_images[:index], False
    else:
        return found_images, True


# get all image json objects from an author_id
def get_images(api, user_info, author_id):
    need_update = True
    images = []
    page = 1
    json = api.users_works(author_id)
    newest_image = json.response[0].id

    if str(author_id) not in user_info["update_info"]:
        last_visit_image = ""
    else:
        last_visit_image = user_info["update_info"][str(author_id)]
    user_info["update_info"][str(author_id)] = newest_image

    while need_update:
        json = api.users_works(author_id, page=page)
        if json.status == "failure":
            break
        found_images = json.response
        found_images, need_update = check_update(found_images, last_visit_image)
        images.extend(found_images)
        page += 1
    return images


# write image to disk
def save_image(session, dir_path, image):
    for i in range(0, image.page_count):
        url = get_download_url(i, image)
        file_name = re.search(r"\d+(_p|_ugoira)\d+\..*", url)[0]
        file_path = dir_path + "\\" + file_name
        print("download image: %s (%s)" % (image.title, file_name))
        response = session.get(url, headers={ "referer": "https://app-api.pixiv.net/"})
        global image_num
        image_num += 1
        with open(file_path, "wb") as f:
            f.write(response.content)
            global total_size
            total_size += len(response.content)


# download all images from an author id
def download_images(api, user_info, author_id):
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))

    author_id = int(author_id)
    author_name = get_author_name(api, author_id)
    if author_name is None:
        print("\nERROR: author id %d does not exist\n" % author_id)
        return
    dir_path = create_directory(author_name, user_info["download_location"])

    print("download for author %s begins\n" % author_name)
    images = get_images(api, user_info, author_id)
    if not images:
        print("author %s is up-to-date\n" % author_name)
        return
    # use all available cores, otherwise specify the number as an argument
    with ThreadPool(THREADS) as pool:
        pool.map(partial(save_image, session, dir_path), images)
    print("\ndownload for author %s completed\n" % author_name)


def main():
    start_time = timeit.default_timer()
    user_info = read_json(USER_FILE)
    api = PixivAPI()
    api.login(user_info["username"], user_info["password"])
    
    print("\nthere are %d authors...\n" % len(user_info["author_ids"]))
    for id in user_info["author_ids"]:
        download_images(api, user_info, id)
    
    update_json(user_info, USER_FILE)
    duration = timeit.default_timer() - start_time
    size_mb = total_size / 1048576
    print("\nSUMMARY")
    print("---------------------------------")
    print("time elapsed:\t%.4f seconds" % duration)
    print("total size:\t%.4f MB" % size_mb)
    print("total images:\t%d images" % image_num)
    print("download speed:\t%.4f MB/s" % (size_mb / duration))

if __name__ == "__main__":
    main()