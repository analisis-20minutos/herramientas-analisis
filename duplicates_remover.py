"""
Pavel Razgovorov (pr18@alu.ua.es), Universidad de Alicante (https://www.ua.es)

This script eliminates the duplicate news from the original corpus we get with Scrapy
"""
import configparser
import contextlib
import datetime
import json
import os
import pathlib
from collections import namedtuple

from datasketch import MinHash, MinHashLSH, LeanMinHash

ADMITTED_CATEGORIES_TXT = 'admitted_categories.txt'
CFG_FILE = 'config.cfg'
DATES_CFG_GROUP = 'dates'
DATES_CFG_FORMAT = '%d/%m/%Y'
DUMP_DIR = f'{pathlib.Path.home()}/dump'
THRESHOLD = 0.7
REGULAR_INTERVAL_DAYS = 60
EDGES_INTERVAL_DAYS = 3

Article = namedtuple('Article', ['title', 'lead', 'body', 'date', 'province', 'url'])


def read_categories_from_file():
    with open(ADMITTED_CATEGORIES_TXT) as f:
        return [x.strip() for x in f.readlines()]


def get_dates_between(start_date, end_date):
    return [start_date + datetime.timedelta(days=x) for x in range(0, (end_date - start_date).days + 1)]


class DuplicateChecker:

    def __init__(self):
        self.minhashes = {}
        self.lsh = MinHashLSH(threshold=THRESHOLD)

    def create_minhashes_reading_articles(self, start_date, end_date):
        """Fills the minhashes dict with the files paths as the keys and the minhashes from the articles bodies as
         the values"""
        for category in read_categories_from_file():
            for date_between in get_dates_between(start_date, end_date):
                try:
                    date_between = date_between.strftime('%Y/%m/%d')
                    current_dir_path = f'{DUMP_DIR}/{category}/{date_between}'
                    for filename in os.listdir(current_dir_path):
                        self._create_minhash_from_file(current_dir_path, filename)
                except FileNotFoundError:
                    pass

    def _create_minhash_from_file(self, current_dir_path, filename):
        file_path = f'{current_dir_path}/{filename}'
        with open(file_path) as f:
            article = Article(**json.load(f))
            if not article.body:
                os.remove(file_path)
                return

            minhash = MinHash()
            for word in article.body.split(' '):
                minhash.update(word.encode('utf8'))
            lean_minhash = LeanMinHash(minhash)
            self.minhashes[file_path] = lean_minhash
            self.lsh.insert(file_path, lean_minhash)

    def find_similar_articles(self):
        """Finds every similar article from the LSH index, and removes it from the index itself as well as the file from
        the disk"""
        for path, minhash in self.minhashes.items():
            # The LSH will find at least the path itself, so we need to filter it
            for similar_article_path in [x for x in self.lsh.query(minhash) if x is not path]:
                print(f'\tremoving similar article from {similar_article_path}')
                self.lsh.remove(similar_article_path)
                with contextlib.suppress(FileNotFoundError):
                    os.remove(similar_article_path)


if __name__ == '__main__':
    cfg_parser = configparser.RawConfigParser()
    cfg_parser.read(CFG_FILE)
    start_cfg_date = datetime.datetime.strptime(cfg_parser.get(DATES_CFG_GROUP, 'start_date'), DATES_CFG_FORMAT)
    end_cfg_date = datetime.datetime.strptime(cfg_parser.get(DATES_CFG_GROUP, 'end_date'), DATES_CFG_FORMAT)

    interval_step = datetime.timedelta(days=REGULAR_INTERVAL_DAYS)
    interval_edge_range = datetime.timedelta(days=EDGES_INTERVAL_DAYS)

    while start_cfg_date < end_cfg_date:
        next_interval = start_cfg_date + interval_step
        print(f'Checking similar articles between {start_cfg_date.strftime(DATES_CFG_FORMAT)}'
              f' and {next_interval.strftime(DATES_CFG_FORMAT)}')
        duplicate_checker = DuplicateChecker()
        duplicate_checker.create_minhashes_reading_articles(start_cfg_date, next_interval)
        duplicate_checker.find_similar_articles()

        print(f'Checking range articles from edges')
        duplicate_checker = DuplicateChecker()
        duplicate_checker.create_minhashes_reading_articles(next_interval - interval_edge_range,
                                                            next_interval + interval_edge_range)
        duplicate_checker.find_similar_articles()

        start_cfg_date += interval_step
