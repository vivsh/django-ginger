
import json
import logging
import random
import os
from os.path import join as joinpath

from django.utils.six.moves.urllib.parse import urlencode, urlsplit
from django.utils.six.moves.urllib.request import urlopen
from django.utils.six import BytesIO

import time
from PIL import Image



logger = logging.getLogger(__name__)


class GoogleImage(object):
    """
    Documentation: "https://developers.google.com/image-search/v1/jsondevguide"
    """

    def __init__(self, target, prefix):
        self.target = target
        self.prefix = prefix
        try:
            os.makedirs(self.target)
        except OSError:
            pass

    def download(self, url):
        logger.info("Downloading %s", url)
        try:
            content = BytesIO(urlopen(url, timeout=10).read())
            img = Image.open(content)
        except IOError as ex:
            logger.error("Failed to download image: %s", str(ex))
        else:
            filename = self.filename(url)
            img.save(filename)

    def filename(self, url):
        head = self.prefix
        i = 0
        filename = joinpath(self.target, "%s.jpg" % head)
        while os.path.exists(filename):
            i += 1
            name = "%s_%d.jpg" % (head, i)
            filename = joinpath(self.target, name)
        return filename

    def search(self, query, total, max_pages=60, **kwargs):
        start = 0
        max_pages = max(max_pages, 60)
        while total > 0 and max_pages > start:
            for image_url in self.get_urls(query, start, **kwargs):
                self.download(image_url)
                yield image_url
                total -= 1
                if total <= 0:
                    break
                time.sleep(random.randint(1, 4))
            start += 4 # 4 pages per page

    def make_query(self, query, start, safe=True, size="large", file_type="jpg"):
        base_url = "https://ajax.googleapis.com/ajax/services/search/images"
        params = {}
        params["q"] = query
        params["start"] = start
        params["v"] = "1.0"
        if file_type:
            params["as_filetype"] = file_type
        if size:
            params["imagesz"] = size
        params["safe"] = "on" if safe else "off"
        return "%s?%s" % (base_url, urlencode(params))

    def get_urls(self, query, start, **kwargs):
        url = self.make_query(query, start, **kwargs)
        logger.info("Fetching results from %s", url)
        response = urlopen(url).read().decode("utf8")
        results = json.loads(response)["responseData"]["results"]
        for item in results:
            yield item["unescapedUrl"]




if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    goog = GoogleImage("student")
    goog.search("india student|exam", 20, safe="off", size="medium", file_type="jpg")
