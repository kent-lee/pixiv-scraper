# Pixiv Scraper

This is my personal project created to download images from [Pixiv](https://www.pixiv.net/) website. The program will download all original images, including images in manga, from specified artists to specified download location, both of which can be edited in `info.json` file. In the download location, the program will create and name directories using the artist names, then download images to the corresponding directories. It checks on artist new uploads, that is, it will only download new images.

![alt text](doc/result.png?raw=true "result")

## Instructions

1. install [Python 3.6+](https://www.python.org/)

2. install library [PixivPy](https://github.com/upbit/pixivpy)

        pip install --user pixivpy

3. edit `info.json` file

4. run `pixiv-scraper.py`

        python pixiv-scraper.py

## Notes

- Pixiv requires users to login in order to see any content, so you need to register an account for this program to work

- if you want to download R-18 images, you need to change `Viewing restriction` in your Pixiv `User settings`

## Issue

HTTP connection closed due to timeout while downloading images. In other words, the program waited too long for the server to provide the image, hence closed the connection. I only encountered this issue once over dozens of tries, and I think this issue was most likely caused by the server rather than the `pixivpy` library or my script. If you encounter this issue, please delete the directory that the image fails to download to and rerun the program again.

## Todo

- refactor code

- add more functionality (e.g. ranking)

- use threads to make the download process faster