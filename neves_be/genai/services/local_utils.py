import hashlib


def generation_cache_id(txt: str) -> int:
    digest = hashlib.blake2b(txt.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, byteorder="big", signed=True)
