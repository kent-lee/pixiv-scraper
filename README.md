# Pixiv Scraper

This is my personal project created to download images from [Pixiv](https://www.pixiv.net/) website. The program will grab the original resolution images, including images in manga and ugoira, from specified users to specified download directory. In the download directory, the program will create and name subdirectories using the user IDs, then save artworks to the corresponding subdirectories. For each artwork, the file modification time are set in order from newest to oldest so that the files can be sorted by modified date. Lastly, when running this program, it will check each user directory to see if an update is needed such that only new uploads will be downloaded.

Note that if you want to download R-18 contents, you need to change `Viewing restriction` in your Pixiv account `User settings`. Also note that the function `user_artworks()` does not require login, but will not retrieve all of the images. The reasons for this are: (1) the R-18 content will be filtered out. (2) the AJAX response does not provide all of the illustration IDs if not logged in. Therefore, it is recommended to register an account.

![alt text](doc/download.gif?raw=true "download")

![alt text](doc/result.png?raw=true "result")

## Features

- simple Pixiv API
- multi-threaded
- downloads all artworks (illustrations + manga) and bookmarks of given user IDs
- updates all artworks (illustrations + manga) and bookmarks of given user IDs
- categorizes downloaded contents in subdirectories
- sets downloaded file modification in order from newest to oldest such that they can be sorted by modified date

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

```
$ python main.py -h

usage: main.py [-h] [-f FILE] [-l] [-u USERNAME] [-p PASSWORD] [-s SAVE_DIR]
               [-a  [ID ...]] [-d all [ID ...]] [-c all [ID ...]] [-t THREADS]
               [-r]
               [{artworks,bookmarks}]

positional arguments:
  {artworks,bookmarks}  set download/config option (default: artworks)

optional arguments:
  -h, --help            show this help message and exit
  -f FILE               load file for this instance (default: data\test.json)
  -l                    list current settings
  -u USERNAME           set username
  -p PASSWORD           set password
  -s SAVE_DIR           set save directory path
  -a  [ID ...]          add user IDs
  -d all [ID ...]       delete user IDs and their directories
  -c all [ID ...]       clear directories of user IDs
  -t THREADS            set number of threads for this instance
  -r                    download content from user IDs (content: OPTION)
```

download artworks for user IDs stored in config file; update users' artworks if directories already exist

```bash
python main.py
```

download bookmarks for user IDs stored in config file; update users' artworks if directories already exist

```bash
python main.py bookmarks
```

delete user IDs and their directories (both artworks and bookmarks), then download artworks for remaining IDs in config file

```bash
python main.py -d 63924 408459 -r
```

add user IDs then download bookmarks for newly added IDs + IDs in config file

```bash
python main.py bookmarks -a 63924 408459 2188232 -r
```

load `temp.json` file in `data` folder (only for this instance), add user IDs to that file, then download artworks for IDs in that file

```bash
python main.py -f data/temp.json -a 63924 408459 2188232 -r
```

clear directories for all user IDs in config file, set threads to 24, then download artworks (i.e. re-download artworks)

```bash
python main.py -c all -t 24 -r
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

## Todo

- add more functionality (e.g. ranking)
