# Pixiv Scraper

This is my personal project created to download images from [Pixiv](https://www.pixiv.net/) website. The program will grab the original resolution images, including images in manga and ugoira, from specified users to specified download directory.

![alt text](doc/download.gif?raw=true "download")

![alt text](doc/result.png?raw=true "result")

## Overview

- when running program, only new uploads will be downloaded
- downloaded artworks are categorized by authors
- modification time of each artwork is set according to upload order

## Note

- if you want to download R-18 contents, you need to change `Viewing restriction` in your Pixiv account `User settings`
- only tested on Windows 10, Ubuntu 18.04, and Manjaro 18.0.4

## Instructions

1. install [Python 3.6+](https://www.python.org/)

2. install `requests` library

    ```bash
    pip install --user requests
    ```

3. edit `config.json` file in `data` folder manually or via command line interface

    - `save directory`: the save directory path
    - `users`: the user ID shown in URL

## Usage

display help message

```bash
$ python main.py -h

usage: main.py [-h] [-f FILE] [-l] [-u USERNAME] [-p PASSWORD] [-s SAVE_DIR]
               [-t THREADS]
               {artwork,bookmark,ranking} ...

positional arguments:
  {artwork,bookmark,ranking}
    artwork             download artworks from user IDs specified in "users"
                        field
    bookmark            download bookmark artworks from user IDs specified in
                        "bookmarks" field
    ranking             download top N ranking artworks based on given
                        conditions

optional arguments:
  -h, --help            show this help message and exit
  -f FILE               load file for this instance (default:
                        data/config.json)
  -l                    list current settings
  -u USERNAME           set username
  -p PASSWORD           set password
  -s SAVE_DIR           set save directory path
  -t THREADS            set number of threads for this instance
```

display `artwork` help message

```bash
$ python main.py artwork -h

usage: main.py artwork [-h] [-a  [ID ...]] [-d all [ID ...]] [-c all [ID ...]]

optional arguments:
  -h, --help       show this help message and exit
  -a  [ID ...]     add user IDs
  -d all [ID ...]  delete user IDs and their directories
  -c all [ID ...]  clear directories of user IDs
```

display `ranking` help message

```bash
$ python main.py ranking -h

usage: main.py ranking [-h] -m MODE -c CONTENT -d YYYYMMDD [-n N]

optional arguments:
  -h, --help   show this help message and exit
  -m MODE      modes: {daily, weekly, monthly, rookie, original, male, female,
               daily_r18, weekly_r18, male_r18, female_r18}
  -c CONTENT   contents: {all, illust, ugoira, manga}
  -d YYYYMMDD  date
  -n N         get top N artworks (default: 20)
```

download artworks from user IDs stored in config file; update users' artworks if directories already exist

```bash
python main.py artwork
```

download bookmark artworks from user IDs stored in config file; update users' artworks if directories already exist

```bash
python main.py bookmark
```

delete user IDs and their directories (IDs in `users` field + artwork directories), then download artworks for remaining IDs in config file

```bash
python main.py artwork -d 63924 408459
```

add user IDs (IDs in `bookmarks` field) then download bookmark artworks for newly added IDs + IDs in config file

```bash
python main.py bookmark -a 63924 408459 2188232
```

load `temp.json` file in `data` folder (only for this instance), add user IDs to that file, then download artworks from IDs in that file

```bash
python main.py artwork -f data/temp.json -a 63924 408459 2188232
```

clear directories for all user IDs in config file, set threads to 24, then download artworks (i.e. re-download artworks)

```bash
python main.py artwork -c all -t 24
```

## Challenges

1. Pixiv uses AJAX request to generate content dynamically, so parsing plain HTML will not work

    - Solution: simulate XHR requests made by JavaScript code to extract data from the server. The XHR requests and responses can be found in browsers' developer tools under Network tab. In Chrome, it has options to filter XHR requests and `Preserve log` to have better observation

2. sometimes the `requests` module will close the program with error `Remote end closed connection without response`. I am not sure the exact cause, but it is most likely due to the high amount of requests sent from the same IP address in a short period of time; hence the server closes the connection

    - Solution: use `session` to download images and allow `session.get` to retry in case of `ConnectionError` exception using `HTTPAdapter` and `Retry` packages

3. update mechanism

    - Attempt 1: download artworks from newest to oldest until an existing file is found on the disk. This does not work well with the multi-threading implementation, as it makes the program a lot more complicated in order to deal with thread stopping condition

    - Attempt 2: record the last visited artwork information for each user to check if update is needed. This does not work if the newest upload was deleted by the user, as the stored information cannot be found in the retrieved HTML. One solution is to record a list of all downloaded artwork information for each user, then compare it with the parsed data, but this wastes a lot of unnecessary space and memory

    - Solution: find the file names while parsing the artwork IDs such that the former can be used to compare with the existing files on disk. If there is a match, then the function will return a list of artworks from newest to the point in which the match was found

4. folder name inconsistency. I originally planned to use user names as the subdirectory names, but there are two problems with this approach: (1) some names are invalid (e.g. containing special characters), and (2), if the users change their names on Pixiv, the program will re-download all contents of the users and leave two directories pointing to the same users

    - Solution: use user IDs to name subdirectories

5. login verification. The program runs fine most of the time, but I have encountered a few times where the program failed to run due to authentication error. This is caused by the `reCAPTCHA v3` verification, and I have yet to figure out a way to bypass it

    - Temporary Solution: if you get this error, just wait for a period of time (e.g. a few days), and the program would work again

## Todo

- implement recommendation system
