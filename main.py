from argparse import ArgumentParser
import utils, pixiv


def init_args():
    parser = ArgumentParser()
    parser.add_argument("-t", dest="threads", type=int, help="change number of threads")
    parser.add_argument("-u", dest="username", help="set pixiv username")
    parser.add_argument("-p", dest="password", help="set pixiv password")
    parser.add_argument("-s", dest="save_dir", help="set save directory path")
    parser.add_argument("-a", nargs="+", dest="add", help="add artist ids", metavar="")
    parser.add_argument("-d", nargs="+", dest="delete", help="delete artist ids", metavar="")
    parser.add_argument("-r", action="store_true", dest="run", help="run program")
    return parser.parse_args()


def main():
    session = pixiv.init_session()
    args = init_args()
    user_file = "data/info.json"
    user = utils.read_json(user_file)
    if args.username: user["username"] = args.username
    if args.password: user["password"] = args.password
    if args.threads: user["threads"] = args.threads
    if args.save_dir: user["save_directory"] = args.save_dir
    if args.add: utils.consume(user["artists"].setdefault(id, "") for id in args.add if pixiv.artist_name(session, id))
    if args.delete:utils.consume(user["artists"].pop(id, None) for id in args.delete)
    if args.run: pixiv.download_artists(session, user)
    utils.write_json(user, user_file)


if __name__ == "__main__":
    main()