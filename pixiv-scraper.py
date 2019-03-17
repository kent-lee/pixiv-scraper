from multiprocessing import Pool
from functools import partial
from pixivpy3 import PixivAPI
import os
import re
import json


# read json file from file path
def get_json(file_path):
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


# returns a json object containing all thumbnail image urls
def illust_pages(api, author_id):
    page = 1
    while True:
        json = api.users_works(author_id, page=page)
        if json.status == "failure":
            break
        page += 1
        # each json has n urls at a time (n = default value in users_works)
        yield json


# get author name from author id
def get_author_name(api, author_id):
    json = api.users(author_id)
    if None in json.response:
        return None
    return json.response[0].name


# create directory and name it using author name
def create_directory(author_name):
    download_location = get_json("info.json")["download_location"]
    directory_path = download_location + "\\" + author_name
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    return directory_path


# get image url in manga
def get_manga_url(count, image):
    try:
        return re.sub("_p0", "_p"+str(count), image.image_urls.large)
    except re.error:
        return re.sub("_ugoira0", "_ugoira"+str(count), image.image_urls.large)


# download all images from an author id
def download_images(api, author_id):
    author_id = int(author_id)
    author_name = get_author_name(api, author_id)
    if author_name is None:
        print("\nERROR: author id %d does not exist\n" % author_id)
        return
    directory_path = create_directory(author_name)

    for json in illust_pages(api, author_id):
        for image in json.response:
            for count in range(0, image.page_count):
                url = get_manga_url(count, image)
                file_name = re.search(r"\d+(_p|_ugoira)\d+\..*", url)[0]
                file_path = directory_path + "\\" + file_name
                if os.path.isfile(file_path):
                    print("\nauthor %s is up-to-date\n" % author_name)
                    return
                api.download(url, path=directory_path)
                print("download image: %s (%s)" % (image.title, file_name))


def main():
    info = get_json("info.json")
    api = PixivAPI()
    api.login(info["username"], info["password"])
    print("\nthere are %d authors...\n" % len(info["author_ids"]))
    # use all available cores, otherwise specify the number as an argument
    with Pool() as pool:
        pool.map(partial(download_images, api), info["author_ids"])


if __name__ == "__main__":
    main()