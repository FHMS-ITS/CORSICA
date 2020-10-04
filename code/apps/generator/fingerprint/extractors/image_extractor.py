import re
from io import open
from PIL import Image


class ImageFingerprintExtractor:
    @staticmethod
    def create_fingerprint(file):
        im = Image.open("{f.local_path}/{f.filename}".format(f=file))
        (width, height) = im.size
        fp = {"t": "i", "w": width, "h": height}
        return fp
