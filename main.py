import time
from lib.pixiv import PixivAPI
from lib.config import Config
from lib import utils, cmd

def download_users(api, config, option, **kwargs):
    start_time = time.time()
    print("logging in to Pixiv...")
    api.login(config.username, config.password)
    if option == "artwork":
        result = api.save_users_artworks(config.users, config.save_dir)
    elif option == "bookmark":
        result = api.save_users_bookmarks(config.bookmarks, config.save_dir)
    elif option == "ranking":
        result = api.save_rankings(**kwargs)
    duration = time.time() - start_time
    size_mb = result["size"] / 1048576
    print("\nSUMMARY")
    print("---------------------------------")
    print(f"time elapsed:\t{duration:.4f} seconds")
    print(f"total size:\t{size_mb:.4f} MB")
    print(f"total artworks:\t{result['count']} artworks")
    print(f"download speed:\t{(size_mb / duration):.4f} MB/s")

def main():
    api = PixivAPI()
    args = cmd.main_parser()
    config = Config(args.f)
    if args.l:
        config.print()
    if args.u:
        config.username = args.u
    if args.p:
        config.password = args.p
    if args.s:
        config.save_dir = args.s
    if args.t:
        api.threads = args.t
    if args.option == "artwork":
        if args.a:
            config.add_users(args.a)
        if args.d:
            config.delete_users(args.d)
        if args.c:
            config.clear_users(args.c)
        download_users(api, config, args.option)
    elif args.option == "bookmark":
        if args.a:
            config.add_bookmarks(args.a)
        if args.d:
            config.delete_bookmarks(args.d)
        if args.c:
            config.clear_bookmarks(args.c)
        download_users(api, config, args.option)
    elif args.option == "ranking":
        params = {
            "mode": args.m,
            "content": args.c,
            "date": args.d,
            "limit": args.n,
            "dir_path": config.save_dir
        }
        download_users(api, config, args.option, **params)
    config.update()

if __name__ == '__main__':
    main()