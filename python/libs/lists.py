#!/usr/bin/env python3

import re
from typing import List, Any


def clear_list(str_list: List[str]) -> List[str]:
    tmp = []
    empty_str = re.compile(r"^\s*$")
    for i in str_list:
        if i and not empty_str.match(i):
            tmp.append(i)
    return tmp


def uniq_list(duplicates: List[Any]) -> List[Any]:
    return list(set(duplicates))


def merge_uniq(src: List[Any], dest: List[Any]) -> List[Any]:
    tmp_src = set(src)
    tmp_dest = set(dest)
    return list(tmp_src.union(tmp_dest))


if __name__ == "__main__":
    raise Exception("This library should not be run as a standalone script")
