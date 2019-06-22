import argparse
import sys, os, time
from lib.pixiv import PixivAPI
from lib.config import Config
from lib import utils

def download_users(api, config, option):
    start_time = time.time()
    print("logging in to Pixiv...")
    api.login(config.username, config.password)
    result = api.save_users(config.users, config.save_dir, option)
    duration = time.time() - start_time
    size_mb = result["size"] / 1048576
    print("\nSUMMARY")
    print("---------------------------------")
    print(f"time elapsed:\t{duration:.4f} seconds")
    print(f"total size:\t{size_mb:.4f} MB")
    print(f"total artworks:\t{result['count']} artworks")
    print(f"download speed:\t{(size_mb / duration):.4f} MB/s")

def commands(api):
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", metavar=("FILE"), default=os.path.join("data", "config.json"), help="load file for this instance (default: %(default)s)")
    parser.add_argument("-l", action="store_true", help="list current settings")
    parser.add_argument("-u", metavar=("USERNAME"), help="set username")
    parser.add_argument("-p", metavar=("PASSWORD"), help="set password")
    parser.add_argument("-s", metavar=("SAVE_DIR"), help="set save directory path")
    parser.add_argument("o", nargs="?", choices=api.options, default="artworks", help="set download/config option (default: artworks)")
    parser.add_argument("-a", metavar=("", "ID"), type=int, nargs="+", help="add user IDs")
    parser.add_argument("-d", metavar=("all", "ID"), nargs="+", help="delete user IDs and their directories")
    parser.add_argument("-c", metavar=("all", "ID"), nargs="+", help="clear directories of user IDs")
    parser.add_argument("-t", metavar=("THREADS"), type=int, help="set number of threads for this instance")
    parser.add_argument("-r", action="store_true", help="download content from user IDs (content: OPTION)")
    return parser.parse_args()

def main():
    api = PixivAPI()
    args = commands(api)
    config = Config(args.f)

    if args.l:
        config.print()
    if args.u:
        config.username = args.u
    if args.p:
        config.password = args.p
    if args.s:
        config.save_dir = args.s
    if args.a:
        config.add_users(args.a)
    if args.d:
        config.delete_users(args.d)
    if args.c:
        config.clear_users(args.c)
    if args.t:
        api.threads = args.t
    if args.r or len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in api.options):
        download_users(api, config, args.o)
    config.update()

if __name__ == "__main__":
    main()