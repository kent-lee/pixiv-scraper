# Pixiv Scraper

This is my personal project created to download images from [Pixiv](https://www.pixiv.net/) website. The program will download all original images, including images in manga, from specified artists to specified download location, both of which can be edited in `info.json` file. In the download location, the program will create and name directories using the artist names, then download images to the corresponding directories. It checks on artist new uploads, so it will only download new images if the directory already exists.

![alt text](doc/download.gif?raw=true "download")

![alt text](doc/result.png?raw=true "result")

## Instructions

1. install [Python 3.6+](https://www.python.org/)

2. install library [PixivPy](https://github.com/upbit/pixivpy)

        pip install --user pixivpy

3. edit `info.json` file

4. go to root directory and run the program

        python pixiv-scraper.py

## Notes

- the program uses threads to download images from multiple authors simultaneously, that is, each thread is responsible for a single author. So, the more authors you have, the more threads the program uses, and ultimately the faster the overall process. Likewise, if you only have one author, the program will run noticeably slower because there is only one thread running

- Pixiv requires users to login in order to see any content, so you need to register an account for this program to work

- if you want to download R-18 images, you need to change `Viewing restriction` in your Pixiv `User settings`

## Todo

- refactor code

- add more functionality (e.g. ranking)