"""
Pavel Razgovorov (pr18@alu.ua.es), Universidad de Alicante (https://www.ua.es)

Spider de Scrapy para el periódico digital 20minutos
"""
import configparser
import datetime
import hashlib
import json
import pathlib
import re
from collections import namedtuple

import scrapy

_20MINS_ARCHIVE_URL = f'https://www.20minutos.es/archivo'
ADMITTED_CATEGORIES_TXT = 'admitted_categories.txt'
CFG_FILE = 'scrapy.cfg'
DATES_CFG_GROUP = 'dates'
DATES_CFG_FORMAT = '%d/%m/%Y'
DUMP_DIR = f'{pathlib.Path.home()}/dump'

Article = namedtuple('Article', ['title', 'lead', 'body', 'date', 'province', 'url'])
moreNewsRegEx = re.compile(r'Consulta aquí más noticias de .+', re.MULTILINE | re.IGNORECASE)
viewFotoRegEx = re.compile(r'ampliar foto', re.MULTILINE | re.IGNORECASE)


def clean_whitespaces_but_no_spaces(string):
    return re.sub(r'\s+', ' ', string).strip()


def write_article(article):
    """Saves the parsed article in a structured directory. The path will have the format {province/year/month/day},
    and the filename is the hashed URL of the article (so if you have downloaded the same article more than once,
    it will override it with the last dump)"""
    dir_path = create_dir(article['province'], article['date'].strftime('%Y/%m/%d'))
    filename = hashlib.sha224(article['url'].encode('utf-8')).hexdigest() + '.json'
    article['date'] = article['date'].isoformat()
    with open(dir_path + filename, 'w') as dump_file:
        encode = json.dumps(article, indent=4, ensure_ascii=False)
        print(encode, file=dump_file)
    return article


def create_dir(province, str_date):
    path = f'{DUMP_DIR}/{province}/{str_date}/'
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)
    return path


def read_categories_from_file():
    with open(ADMITTED_CATEGORIES_TXT) as f:
        return [x.strip() for x in f.readlines()]


def get_dates_between(start_date, end_date):
    return [start_date + datetime.timedelta(days=x) for x in range(0, (end_date - start_date).days + 1)]


class ArticlesSpider(scrapy.Spider):
    name = '20minutos'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.admitted_categories = read_categories_from_file()

    def start_requests(self):
        config_parser = configparser.RawConfigParser()
        config_parser.read(CFG_FILE)
        dates_between = get_dates_between(
            datetime.datetime.strptime(config_parser.get(DATES_CFG_GROUP, 'start_date'), DATES_CFG_FORMAT),
            datetime.datetime.strptime(config_parser.get(DATES_CFG_GROUP, 'end_date'), DATES_CFG_FORMAT))

        for date in dates_between:
            formatted_date = date.strftime("%Y/%m/%d")
            yield scrapy.Request(url=(f'{_20MINS_ARCHIVE_URL}/{formatted_date}/'), callback=self.parse)

    def parse(self, response):
        for category in response.css('.normal-list:first-child > .item'):
            category_name = category.css('.item::text').extract_first().strip()
            if category_name in self.admitted_categories:
                yield from self.parse_category(category, category_name)

    def parse_category(self, category, category_name):
        category_urls = category.css('.sub-list a::attr(href)').extract()
        for category_url in category_urls:
            yield (scrapy.Request(url=category_url, callback=lambda r: self.parse_article(r, category_name)))

    @staticmethod
    def parse_article(response, category_name):
        title = ' '.join(response.css('.article-title *::text').extract())
        lead = ' '.join(response.css('.gtm-article-lead *::text').extract())
        body = ' '.join(response.css('.gtm-article-text::text, '
                                     '.gtm-article-text > p *::text, '
                                     '.gtm-article-text span *::text, '
                                     '.gtm-article-text strong *::text, '
                                     '.gtm-article-text h2 *::text, '
                                     '.gtm-article-text a *::text, '
                                     '.gtm-article-text .quote *::text').extract())
        # Text post-cleaning (easier than modifying css selector)
        body = moreNewsRegEx.sub('', viewFotoRegEx.sub('', body))
        date = datetime.datetime.strptime(response.css('.date a::text').extract_first(), '%d.%m.%Y')

        article = Article(title=clean_whitespaces_but_no_spaces(title),
                          lead=clean_whitespaces_but_no_spaces(lead),
                          body=clean_whitespaces_but_no_spaces(body),
                          date=date,
                          province=category_name,
                          url=response.url)
        yield write_article(article._asdict())
