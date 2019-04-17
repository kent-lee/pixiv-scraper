import itertools
import collections
import json
import os
import time


def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(data, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def mkdir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path


# https://docs.python.org/3/library/itertools.html#itertools-recipes
def consume(iterator, n=None):
    if n is None:
        collections.deque(iterator, maxlen=0)
    else:
        next(itertools.islice(iterator, n, n), None)


# https://docs.python.org/3/library/itertools.html#itertools-recipes
def flatten(listOfLists):
    return itertools.chain.from_iterable(listOfLists)


# set the access and modified times of files for sorting purpose
def set_modified_times(files, dir_path):
    ts = time.time()
    for i,f in enumerate(files):
        file_path = os.path.join(dir_path, f)
        os.utime(file_path, (ts - i, ts - i))