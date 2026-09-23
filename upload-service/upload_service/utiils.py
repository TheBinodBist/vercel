import os
import random

MAX_LEN = 5
SUBSET = "123456789qwertyuiopasdfghjklzxcvbnm"


def generate() -> str:
    return "".join(random.choice(SUBSET) for _ in range(MAX_LEN))


def get_all_files(directory: str)-> list[str]:
    all_files = []
    for root, directories, files in os.walk(directory):
        for f in files:
            all_files.append(os.path.join((root,f)))
        return  all_files