import itertools
import os

from typing import List


def get_files_in_set(root: str, file_names:  List[str]) -> List[str]:
    files_in_sets = [open(os.path.join(root, f), 'r').readlines() for f in
                     file_names]
    files_in_sets = list(itertools.chain(*files_in_sets))
    files_in_sets = [l[:-1] for l in files_in_sets]
    return files_in_sets