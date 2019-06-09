# Pixiv Scraper

This is my personal project created to download images from [Pixiv](https://www.pixiv.net/) website. The program will grab the highest resolution images, including images in manga and ugoira, from specified artists to specified download directory. In the download directory, the program will create and name subdirectories using the artist IDs, then save artworks to the corresponding subdirectories. For each artwork, the file modification time are set in order from newest to oldest so that you can sort files by modified date. Lastly, when running this program, it will check each artist directory to see if an update is needed such that only new uploads will be downloaded.

Note that the program can be run without logging in, but it is not going to retrieve all of the images. The reasons for this are: (1) the R-18 content will be filtered out. (2) the AJAX response does not provide all of the illustration IDs if not logged in. Therefore, it is not recommended to do so. Also, if you want to download R-18 contents, you need to change `Viewing restriction` in your Pixiv account `User settings`.

![alt text](doc/download.gif?raw=true "download")

![alt text](doc/result.png?raw=true "result")

## Instructions

1. install [Python 3.6+](https://www.python.org/)

2. install `requests` library

    ```bash
    pip install --user requests
    ```

3. edit `config.json` file in `data` folder manually or via command line interface

    - `artists`: the artist id shown in URL

    - `save directory`: the save directory path

## Usage

display help message

```bash
$ python main.py -h

usage: main.py [-h] [-f FILE] [-l] [-u USERNAME] [-p PASSWORD] [-s SAVE_DIR]
               [-a  [ID ...]] [-d all [ID ...]] [-c all [ID ...]] [-t THREADS]
               [-r]

optional arguments:
  -h, --help       show this help message and exit
  -f FILE          load config file
  -l               list current settings
  -u USERNAME      set username
  -p PASSWORD      set password
  -s SAVE_DIR      set save directory path
  -a  [ID ...]     add artist ids
  -d all [ID ...]  delete artist ids and their directories
  -c all [ID ...]  clear artist directories
  -t THREADS       set the number of threads
  -r               run program

```

run the program with current configuration (i.e. update artists' artworks)

```bash
python main.py
```

add artist IDs then run the program

```bash
python main.py -a 63924 408459 2188232 -r
```

load `temp.json` file in `data` folder then add artist IDs. Note that `temp.json` is only used for this instance and is not a replacement for the default `config.json` file

```bash
python main.py -f data/temp.json -a 63924 408459 2188232
```

clear update information (i.e. re-download images), set threads to 24, then run the program

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

    - Attempt 2: record the last visited artwork information for each artist to check if update is needed. This does not work if the newest upload was deleted by the artist, as the stored information cannot be found in the retrieved HTML. One solution is to record a list of all downloaded artwork information for each artist, then compare it with the parsed data, but this wastes a lot of unnecessary space and memory

    - Solution: find the file names while parsing the artwork IDs such that the former can be used to compare with the existing files on disk. If there is a match, then the function will return a list of artworks from newest to the point in which the match was found.

## Todo

- add more functionality (e.g. ranking)
