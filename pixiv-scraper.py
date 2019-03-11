from pixivpy3 import PixivAPI
import os
import re
import json


def get_json(file_path):
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def illust_pages(api, author_id):
    page = 1
    while True:
        json = api.users_works(author_id, page=page)
        page += 1
        if json.status == "failure":
            break
        yield json


def get_author_name(api, author_id):
    json = api.users(author_id)
    if None in json.response:
        return None
    return json.response[0].name


def create_directory(api, author_name, download_location):
    directory_path = download_location + "\\" + author_name
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    return directory_path


def parse_url(count, image):
    try:
        return re.sub("_p0", "_p"+str(count), image.image_urls.large)
    except re.error:
        return re.sub("_ugoira0", "_ugoira"+str(count), image.image_urls.large)


def download_images(api, author_id, download_location):
    author_name = get_author_name(api, author_id)
    if author_name is None:
        print("\nERROR: author id %d does not exist\n" % author_id)
        return
    directory_path = create_directory(api, author_name, download_location)
    print("\ndownload for author %s begins\n" %  author_name)
    for json in illust_pages(api, author_id):
        for image in json.response:
            for count in range(0, image.page_count):
                url = parse_url(count, image)
                file_name = re.search(r"\d+(_p|_ugoira)\d+\..*", url)[0]
                file_path = directory_path + "\\" + file_name
                if os.path.isfile(file_path):
                    print("author %s is up-to-date\n" % author_name)
                    return
                api.download(url, path=directory_path)
                print("download image: %s (%s)" % (image.title, file_name))
    print("\ndownload for author %s completed\n" %  author_name)


def main():
    info = get_json("info.json")
    api = PixivAPI()
    api.login(info["username"], info["password"])

    print("\nthere are %d authors...\n" % len(info["author_ids"]))
    for id in info["author_ids"]:
        download_images(api, int(id), info["download_location"])


if __name__ == "__main__":
    main()