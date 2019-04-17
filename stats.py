import time


start_time = 0
files = 0
files_size = 0
KB = 1024
MB = 1048576
GB = 1073741824


def init_stats():
    global start_time, files, files_size
    start_time = time.time()
    files = files_size = 0


def update_files():
    global files
    files += 1


def update_size(data):
    global files_size
    files_size += data


def display_stats():
    duration = time.time() - start_time 
    size_mb = files_size / MB
    print("\nSUMMARY")
    print("---------------------------------")
    print(f"time elapsed:\t{duration:.4f} seconds")
    print(f"total size:\t{size_mb:.4f} MB")
    print(f"total artworks:\t{files} artworks")
    print(f"download speed:\t{(size_mb / duration):.4f} MB/s")