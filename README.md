# Pixiv Scraper

This is my personal project created to download images from [Pixiv](https://www.pixiv.net/) website. The program will grab the highest resolution images, including images in manga and ugoira, from specified artists to specified download location. In the download location, the program will create and name directories using the artist names, then download images to the corresponding directories. It stores update information for each artist, so it will only download new uploads.

The program uses threads to download images; the number of threads can be modified via command line interface.

![alt text](doc/download.gif?raw=true "download")

![alt text](doc/result.png?raw=true "result")

## Instructions

1. install [Python 3.6+](https://www.python.org/)

2. install `requests` library

    ```bash
    pip install --user requests
    ```

3. edit `info.json` file in `data` folder manually or via command line interface

    - `artists`: the artist id shown in URL

    - `save directory`: the save directory path

4. go to root directory and run the program

    ```bash
    python main.py -r
    ```

## Command line interface

display help message

```bash
$ python main.py -h

usage: main.py [-h] [-t THREADS] [-u USERNAME] [-p PASSWORD] [-s SAVE_DIR]
       [-a  [...]] [-d  [...]] [-r]

optional arguments:
-h, --help   show this help message and exit
-t THREADS   change number of threads
-u USERNAME  set pixiv username
-p PASSWORD  set pixiv password
-s SAVE_DIR  set save directory path
-a  [ ...]   add artist ids
-d  [ ...]   delete artist ids
-r           run program
```

add artist ids and run the program

```bash
python main.py -a 63924 408459 2188232 -r
```

## Notes

- I could not figure out a way to bypass the login requirement, so you need to have an account for this program to work.

- if you want to download R-18 images, you need to change `Viewing restriction` in your Pixiv `User settings`

## Challenges

1. Pixiv uses `AJAX` script to generate content dynamically, so parsing plain `HTML` will not work

    - Solution: simulate `XHR` requests made by `JavaScript` code to extract data from the server. The `XHR` requests and responses can be found in browsers' developer tools under `Network` tab. In `Chrome`, you can filter `XHR` and set the tool to `Preserve log` to have better observation

2. sometimes the `requests` module will close the program with error `Remote end closed connection without response`. I am not sure the exact cause, but it is most likely due to the high amount of requests sent from the same IP address in a short period of time; hence the server closes the connection

    - Solution: use `session` to download images and allow `session.get` to retry in case of `ConnectionError` exception using `HTTPAdapter` and `Retry` packages

## Todo

- add more functionality (e.g. ranking)