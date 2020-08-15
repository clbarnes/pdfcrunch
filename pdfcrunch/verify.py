import logging
import hashlib

logger = logging.getLogger(__name__)
BLOCKSIZE = 65536


def hash_file(f):
    if not hasattr(f, "read"):
        with open(f, "rb") as f_obj:
            return hash_file(f_obj)

    hasher = hashlib.md5()
    buf = f.read(BLOCKSIZE)
    while len(buf) > 0:
        hasher.update(buf)
        buf = f.read(BLOCKSIZE)
    return hasher.hexdigest()


def verify_file(f, expected):
    """Check a file's MD5sum against the given hex digest"""
    actual = hash_file(f)
    if actual != expected:
        logger.warning("File does not have the expected hash. Is it correct?")
