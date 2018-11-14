"""
Pavel Razgovorov (pr18@alu.ua.es), Universidad de Alicante (https://www.ua.es)

Set of simple scripts that generate CSVs with information collected from the corpus in order to be able to be processed
afterwards.

The scripts are quite repetitive and surely could be done better, but the purpose here was to make them quickly
with an ad-hoc intention (that is, to be used only once).
"""
import configparser
import datetime
import fnmatch
import json
import os
from collections import namedtuple
from pathlib import Path

ADMITTED_CATEGORIES_TXT = 'admitted_categories.txt'
CFG_FILE = 'config.cfg'
DATES_CFG_GROUP = 'dates'
DATES_CFG_FORMAT = '%d/%m/%Y'
DATES_FILE_FORMAT = '%Y/%m/%d'
DATES_SQL_FORMAT = '%Y-%m-%d'
DUMP_DIR = f'{str(Path.home())}/dump-processed'
JSON_FILE_PATTERN = '*.json'

Article = namedtuple('Article', ['title', 'lead', 'body', 'date', 'province', 'url'])


def read_categories_from_file():
    with open(ADMITTED_CATEGORIES_TXT) as f:
        return [x.strip() for x in f.readlines()]


def get_dates_between(start_date, end_date):
    return [start_date + datetime.timedelta(days=x) for x in range(0, (end_date - start_date).days + 1)]


def get_dates_from_cfg():
    cfg_parser = configparser.RawConfigParser()
    cfg_parser.read(CFG_FILE)
    start_cfg_date = datetime.datetime.strptime(
        cfg_parser.get(DATES_CFG_GROUP, 'start_date'), DATES_CFG_FORMAT)
    end_cfg_date = datetime.datetime.strptime(
        cfg_parser.get(DATES_CFG_GROUP, 'end_date'), DATES_CFG_FORMAT)
    return start_cfg_date, end_cfg_date


def get_news_count():
    """Generates a CSV with the amount of news by category per year"""
    start_cfg_date, end_cfg_date = get_dates_from_cfg()

    total = 0
    with open('news_count.csv', 'w') as csv:
        print('category;date;news_count', file=csv)
        for category in read_categories_from_file():
            print(f'Counting {category} category...')
            for date_between in get_dates_between(start_cfg_date, end_cfg_date):
                try:
                    current_dir_path = f'{DUMP_DIR}/{category}/{date_between.strftime(DATES_FILE_FORMAT)}'
                    files_count = len(fnmatch.filter(os.listdir(current_dir_path), JSON_FILE_PATTERN))
                    total += files_count
                    print(f'{category};{date_between.strftime(DATES_SQL_FORMAT)};{files_count}', file=csv)
                except FileNotFoundError:
                    pass
    print('Total: ', total)


def get_words_count_per_year(text='lemmatized_text', csv_suffix=''):
    """Generates a CSV with the amount of total words per year"""
    start_cfg_date, end_cfg_date = get_dates_from_cfg()

    for year in range(start_cfg_date.year, end_cfg_date.year + 1):
        counts = {}
        for category in read_categories_from_file():
            print(f'Extracting {category}\'s words...')
            for date_between in get_dates_between(start_cfg_date, end_cfg_date):
                if date_between.year == year:
                    print(f'\tExtracting {date_between}\'s words...', end='\r')
                    try:
                        current_dir_path = f'{DUMP_DIR}/{category}/{date_between.strftime(DATES_FILE_FORMAT)}'
                        for filename in os.listdir(current_dir_path):
                            file_path = f'{current_dir_path}/{filename}'
                            with open(file_path) as f:
                                article = json.load(f)
                                for part in ['title', 'lead', 'body']:
                                    for word in article[part][text].split(' '):
                                        if word in counts:
                                            counts[word] += 1
                                        else:
                                            counts[word] = 1
                    except FileNotFoundError:
                        pass
            print()
        with open(f'words_count_{year}{csv_suffix}.csv', 'w') as f:
            for word, count in counts.items():
                print(f'{year};{word};{count}', file=f)


def get_words_count_per_season(text='lemmatized_text', csv_suffix=''):
    """Generates a CSV with the amount of total words per season"""
    Season = namedtuple("Season", ['name', 'start_date', 'end_date'])
    dummy_leap_year = 2000
    seasons = [Season('winter', datetime.date(dummy_leap_year, 1, 1), datetime.date(dummy_leap_year, 3, 20)),
               Season('spring', datetime.date(dummy_leap_year, 3, 21), datetime.date(dummy_leap_year, 6, 20)),
               Season('summer', datetime.date(dummy_leap_year, 6, 21), datetime.date(dummy_leap_year, 9, 20)),
               Season('autumn', datetime.date(dummy_leap_year, 9, 21), datetime.date(dummy_leap_year, 12, 20)),
               Season('winter2', datetime.date(dummy_leap_year, 12, 21), datetime.date(dummy_leap_year, 12, 31))]

    def get_season(now):
        if isinstance(now, datetime.datetime):
            now = now.date()
        now = now.replace(year=dummy_leap_year)
        return next(s for s in seasons if s.start_date <= now <= s.end_date)

    start_cfg_date, end_cfg_date = get_dates_from_cfg()

    for season in seasons:
        counts = {}
        for category in read_categories_from_file():
            print(f'Extracting {category}\'s words...')
            for date_between in get_dates_between(start_cfg_date, end_cfg_date):
                current_season = get_season(date_between)
                if current_season.name == season.name:
                    print(f'\tExtracting {date_between}\'s words...', end='\r')
                    try:
                        current_dir_path = f'{DUMP_DIR}/{category}/{date_between.strftime(DATES_FILE_FORMAT)}'
                        for filename in os.listdir(current_dir_path):
                            file_path = f'{current_dir_path}/{filename}'
                            with open(file_path) as f:
                                article = json.load(f)
                                for part in ['title', 'lead', 'body']:
                                    for word in article[part][text].split(' '):
                                        if word in counts:
                                            counts[word] += 1
                                        else:
                                            counts[word] = 1
                    except FileNotFoundError:
                        pass
            print()
        with open(f'words_count_{season.name}{csv_suffix}.csv', 'w') as f:
            for word, count in counts.items():
                print(f'{season.name};{word};{count}', file=f)


def get_words_count_per_category():
    """Generates a CSV with the amount of total words per category"""
    start_cfg_date, end_cfg_date = get_dates_from_cfg()

    for category in read_categories_from_file():
        counts = {}
        counts_reduced = {}
        print(f'Extracting {category}\'s words...')
        for date_between in get_dates_between(start_cfg_date, end_cfg_date):
            print(f'\tExtracting {date_between}\'s words...', end='\r')
            try:
                current_dir_path = f'{DUMP_DIR}/{category}/{date_between.strftime(DATES_FILE_FORMAT)}'
                for filename in os.listdir(current_dir_path):
                    file_path = f'{current_dir_path}/{filename}'
                    with open(file_path) as f:
                        article = json.load(f)
                        for part in ['title', 'lead', 'body']:
                            for word in article[part]['lemmatized_text'].split(' '):
                                if word in counts:
                                    counts[word] += 1
                                else:
                                    counts[word] = 1
                            for word in article[part]['lemmatized_text_reduced'].split(' '):
                                if word in counts_reduced:
                                    counts_reduced[word] += 1
                                else:
                                    counts_reduced[word] = 1
            except FileNotFoundError:
                pass
        print()
        with open(f'words_count_{category}.csv', 'w') as csv_out, \
                open(f'words_count_{category}_reduced.csv', 'w') as csv_reduced:
            for word, count in counts.items():
                print(f'{category};{word};{count}', file=csv_out)
            for word, count in counts_reduced.items():
                print(f'{category};{word};{count}', file=csv_reduced)


def get_words_count_total(text='lemmatized_text', csv_suffix=''):
    """Generates a CSV with the amount of total words"""
    start_cfg_date, end_cfg_date = get_dates_from_cfg()

    counts = {}
    for category in read_categories_from_file():
        print(f'Extracting {category}\'s words...')
        for date_between in get_dates_between(start_cfg_date, end_cfg_date):
            print(f'\tExtracting {date_between}\'s words...', end='\r')
            try:
                current_dir_path = f'{DUMP_DIR}/{category}/{date_between.strftime(DATES_FILE_FORMAT)}'
                for filename in os.listdir(current_dir_path):
                    file_path = f'{current_dir_path}/{filename}'
                    with open(file_path) as f:
                        article = json.load(f)
                        for part in ['title', 'lead', 'body']:
                            for word in article[part][text].split(' '):
                                if word in counts:
                                    counts[word] += 1
                                else:
                                    counts[word] = 1
            except FileNotFoundError:
                pass
        print()
    with open(f'words_count_total{csv_suffix}.csv', 'w') as f:
        for word, count in counts.items():
            print(f'total;{word};{count}', file=f)


def get_necs_count_per_year():
    """Generates a CSV with the amount of Named Entities per year"""
    start_cfg_date, end_cfg_date = get_dates_from_cfg()

    for year in range(start_cfg_date.year, end_cfg_date.year + 1):
        counts = {}
        for category in read_categories_from_file():
            print(f'Extracting {category}\'s words...')
            for date_between in get_dates_between(start_cfg_date, end_cfg_date):
                if date_between.year == year:
                    print(f'\tExtracting {date_between}\'s words...', end='\r')
                    try:
                        current_dir_path = f'{DUMP_DIR}/{category}/{date_between.strftime(DATES_FILE_FORMAT)}'
                        for filename in os.listdir(current_dir_path):
                            file_path = f'{current_dir_path}/{filename}'
                            with open(file_path) as f:
                                article = json.load(f)
                                for part in ['title', 'lead', 'body']:
                                    for text in ['persons', 'locations', 'organizations', 'others']:
                                        for nec in article[part][text]:
                                            if nec in counts:
                                                counts[nec] += 1
                                            else:
                                                counts[nec] = 1
                    except FileNotFoundError:
                        pass
            print()
        with open(f'necs_count_{year}.csv', 'w') as csv_out:
            for nec, ocurrences in counts.items():
                print(f'{year};{nec};{ocurrences}', file=csv_out)


def get_necs_count_per_category():
    """Generates a CSV with the amount of Named Entities per category"""
    start_cfg_date, end_cfg_date = get_dates_from_cfg()

    for category in read_categories_from_file():
        counts = {}
        print(f'Extracting {category}\'s words...')
        for date_between in get_dates_between(start_cfg_date, end_cfg_date):
            print(f'\tExtracting {date_between}\'s words...', end='\r')
            try:
                current_dir_path = f'{DUMP_DIR}/{category}/{date_between.strftime(DATES_FILE_FORMAT)}'
                for filename in os.listdir(current_dir_path):
                    file_path = f'{current_dir_path}/{filename}'
                    with open(file_path) as f:
                        article = json.load(f)
                        for part in ['title', 'lead', 'body']:
                            for text in ['persons', 'locations', 'organizations', 'others']:
                                for nec in article[part][text]:
                                    if nec in counts:
                                        counts[nec] += 1
                                    else:
                                        counts[nec] = 1
            except FileNotFoundError:
                pass
        print()
        with open(f'necs_count_{category}.csv', 'w') as csv_out:
            for nec, ocurrences in counts.items():
                print(f'{category};{nec};{ocurrences}', file=csv_out)


def get_news_from_topics(text='lemmatized_text', csv_suffix='', topics=set(), func=all):
    """Generates a CSV with article entries which contains the topics passed by argument

    Args:
        :param text: JSON field where you extract the text to analyze from (raw_text, lemmatized_text,
                     lemmatized_text_reduced)
        :param csv_suffix: if you want to add a suffix to the generated CSV file
        :param topics: set of topics to look for
        :param func: can be `all` (default) to add an entry if ALL the topics were found, or `any`
                     if AT LEAST ONE were.
    """
    Appereance = namedtuple("Appereance", ["date", "province", "article"])
    start_cfg_date, end_cfg_date = get_dates_from_cfg()

    appereances = set()
    for category in read_categories_from_file():
        print(f'Extracting {category}\'s news...')
        for date_between in get_dates_between(start_cfg_date, end_cfg_date):
            print(f'\tExtracting {date_between}\'s news...', end='\r')
            try:
                current_dir_path = f'{DUMP_DIR}/{category}/{date_between.strftime(DATES_FILE_FORMAT)}'
                for filename in os.listdir(current_dir_path):
                    file_path = f'{current_dir_path}/{filename}'
                    with open(file_path) as f:
                        article = json.load(f)
                        for part in ['title', 'lead', 'body']:
                            if func(topic in article[part][text] for topic in topics):
                                appereances.add(Appereance(date_between, category, article['url']))
            except FileNotFoundError:
                pass
        print()
    with open(f'news_appereances{csv_suffix}.csv', 'w') as f:
        for appereance in appereances:
            print(f'{appereance.province};{appereance.date.strftime(DATES_SQL_FORMAT)};{appereance.article}', file=f)


def get_news_from_topics_with_count(text='lemmatized_text', csv_suffix='', topics=set(), raw_topics=set()):
    """Same as get_news_from_topics, but it counts the amount of topics found and the ratio between that amount and
    all the article's words

    Args:
        :param text: JSON field where you extract the text to analyze from (lemmatized_text, lemmatized_text_reduced)
        :param csv_suffix: if you want to add a suffix to the generated CSV file
        :param topics: set of topics to look for
        :param raw_topics: set of topics to look for, but exclusively for the raw_text
    """
    Appereance = namedtuple("Appereance", ["date", "province", "article", "counts", "ratio_per_day"])
    start_cfg_date, end_cfg_date = get_dates_from_cfg()

    appereances = set()
    for category in read_categories_from_file():
        print(f'Extracting {category}\'s news...')
        for date_between in get_dates_between(start_cfg_date, end_cfg_date):
            print(f'\tExtracting {date_between}\'s news...', end='\r')
            try:
                current_dir_path = f'{DUMP_DIR}/{category}/{date_between.strftime(DATES_FILE_FORMAT)}'
                words_per_day = 0
                for filename in os.listdir(current_dir_path):
                    file_path = f'{current_dir_path}/{filename}'
                    with open(file_path) as f:
                        article = json.load(f)
                        for part in ['title', 'lead', 'body']:
                            words_per_day += len(article[part][text].split(' '))
                for filename in os.listdir(current_dir_path):
                    file_path = f'{current_dir_path}/{filename}'
                    with open(file_path) as f:
                        article = json.load(f)
                        counts = 0
                        for part in ['title', 'lead', 'body']:
                            for topic in topics:
                                counts += article[part][text].count(topic)
                            for raw_topic in raw_topics:
                                counts += article[part]['raw_text'].lower().count(raw_topic)
                        if counts > 0:
                            appereances.add(
                                Appereance(date_between, category, article['url'], counts, counts / words_per_day))
            except FileNotFoundError:
                pass
        print()
    with open(f'news_appereances{csv_suffix}.csv', 'w') as f:
        for appereance in appereances:
            print(f'{appereance.province};{appereance.date.strftime(DATES_SQL_FORMAT)};'
                  f'{appereance.article};{appereance.counts};{appereance.ratio_per_day}', file=f)


def get_ttrs_from_articles_per_year():
    """Generates a CSV which gives the TTR (Type-Token Ratio) mean of all the articles per year"""
    start_cfg_date, end_cfg_date = get_dates_from_cfg()

    ttrs_mean = {}
    ttrs_mean_reduced = {}
    for year in range(start_cfg_date.year, end_cfg_date.year + 1):
        ttrs = []
        ttrs_reduced = []
        articles_readen = 0
        for category in read_categories_from_file():
            print(f'Extracting {category}\'s news...')
            for date_between in get_dates_between(start_cfg_date, end_cfg_date):
                if date_between.year == year:
                    print(f'\tExtracting {date_between}\'s news...', end='\r')
                    try:
                        current_dir_path = f'{DUMP_DIR}/{category}/{date_between.strftime(DATES_FILE_FORMAT)}'
                        for filename in os.listdir(current_dir_path):
                            file_path = f'{current_dir_path}/{filename}'
                            with open(file_path) as f:
                                article = json.load(f)
                                counts = {}
                                counts_reduced = {}
                                for part in ['title', 'lead', 'body']:
                                    for word in article[part]['lemmatized_text'].split(' '):
                                        if word in counts:
                                            counts[word] += 1
                                        else:
                                            counts[word] = 1
                                    for word in article[part]['lemmatized_text_reduced'].split(' '):
                                        if word in counts_reduced:
                                            counts_reduced[word] += 1
                                        else:
                                            counts_reduced[word] = 1
                                ttrs.append(len(counts) / sum(counts.values()))
                                ttrs_reduced.append(len(counts_reduced) / sum(counts_reduced.values()))
                                articles_readen += 1
                    except FileNotFoundError:
                        pass
            print()
        ttrs_mean[year] = (sum(ttrs) / articles_readen)
        ttrs_mean_reduced[year] = (sum(ttrs_reduced) / articles_readen)
    with open('ttrs_per_year.csv', 'w') as csv_out, open('ttrs_per_year_reduced.csv', 'w') as csv_reduced:
        for year, ttr_mean in ttrs_mean.items():
            print(f'{year};{ttr_mean}', file=csv_out)
        for year, ttr_mean_reduced in ttrs_mean_reduced.items():
            print(f'{year};{ttr_mean_reduced}', file=csv_reduced)


def get_ttrs_from_articles_per_province():
    """Generates a CSV which gives the TTR (Type-Token Ratio) mean of all the articles per province"""
    start_cfg_date, end_cfg_date = get_dates_from_cfg()

    ttrs_mean = {}
    ttrs_mean_reduced = {}
    for category in read_categories_from_file():
        print(f'Extracting {category}\'s news...')
        ttrs = []
        ttrs_reduced = []
        articles_readen = 0
        for date_between in get_dates_between(start_cfg_date, end_cfg_date):
            print(f'\tExtracting {date_between}\'s news...', end='\r')
            try:
                current_dir_path = f'{DUMP_DIR}/{category}/{date_between.strftime(DATES_FILE_FORMAT)}'
                for filename in os.listdir(current_dir_path):
                    file_path = f'{current_dir_path}/{filename}'
                    with open(file_path) as f:
                        article = json.load(f)
                        counts = {}
                        counts_reduced = {}
                        for part in ['title', 'lead', 'body']:
                            for word in article[part]['lemmatized_text'].split(' '):
                                if word in counts:
                                    counts[word] += 1
                                else:
                                    counts[word] = 1
                            for word in article[part]['lemmatized_text_reduced'].split(' '):
                                if word in counts_reduced:
                                    counts_reduced[word] += 1
                                else:
                                    counts_reduced[word] = 1
                        ttrs.append(len(counts) / sum(counts.values()))
                        ttrs_reduced.append(len(counts_reduced) / sum(counts_reduced.values()))
                        articles_readen += 1
            except FileNotFoundError:
                pass
        print()
        ttrs_mean[category] = (sum(ttrs) / articles_readen)
        ttrs_mean_reduced[category] = (sum(ttrs_reduced) / articles_readen)
    with open('ttrs_per_category.csv', 'w') as csv_out, open('ttrs_per_category_reduced.csv', 'w') as csv_reduced:
        for year, ttr_mean in ttrs_mean.items():
            print(f'{year};{ttr_mean}', file=csv_out)
        for year, ttr_mean_reduced in ttrs_mean_reduced.items():
            print(f'{year};{ttr_mean_reduced}', file=csv_reduced)


def get_ttrs_from_articles_total():
    """Prints the TTR (Type-Token Ratio) mean of all the articles"""
    start_cfg_date, end_cfg_date = get_dates_from_cfg()

    ttrs = []
    ttrs_reduced = []
    articles_readen = 0
    for category in read_categories_from_file():
        print(f'Extracting {category}\'s news...')
        for date_between in get_dates_between(start_cfg_date, end_cfg_date):
            print(f'\tExtracting {date_between}\'s news...', end='\r')
            try:
                current_dir_path = f'{DUMP_DIR}/{category}/{date_between.strftime(DATES_FILE_FORMAT)}'
                for filename in os.listdir(current_dir_path):
                    file_path = f'{current_dir_path}/{filename}'
                    with open(file_path) as f:
                        article = json.load(f)
                        counts = {}
                        counts_reduced = {}
                        for part in ['title', 'lead', 'body']:
                            for word in article[part]['lemmatized_text'].split(' '):
                                if word in counts:
                                    counts[word] += 1
                                else:
                                    counts[word] = 1
                            for word in article[part]['lemmatized_text_reduced'].split(' '):
                                if word in counts_reduced:
                                    counts_reduced[word] += 1
                                else:
                                    counts_reduced[word] = 1
                        ttrs.append(len(counts) / sum(counts.values()))
                        ttrs_reduced.append(len(counts_reduced) / sum(counts_reduced.values()))
                        articles_readen += 1
            except FileNotFoundError:
                pass
        print()
    print('normal: ', sum(ttrs) / articles_readen)
    print('reduced: ', sum(ttrs_reduced) / articles_readen)


def get_anglicisms_from_articles_per_year():
    """Generates a CSV which gives the anglicisms usage percentage of all the articles per year"""
    start_cfg_date, end_cfg_date = get_dates_from_cfg()

    anglicisms_mean = {}
    anglicisms_mean_reduced = {}
    with open("anglicisms.txt") as anglicisms_file:
        anglicisms_list = [line.strip() for line in anglicisms_file.readlines()]
        for year in range(start_cfg_date.year, end_cfg_date.year + 1):
            anglicisms = []
            anglicisms_reduced = []
            articles_readen = 0
            for category in read_categories_from_file():
                print(f'Extracting {category}\'s news...')
                for date_between in get_dates_between(start_cfg_date, end_cfg_date):
                    if date_between.year == year:
                        print(f'\tExtracting {date_between}\'s news...', end='\r')
                        try:
                            current_dir_path = f'{DUMP_DIR}/{category}/{date_between.strftime(DATES_FILE_FORMAT)}'
                            for filename in os.listdir(current_dir_path):
                                file_path = f'{current_dir_path}/{filename}'
                                with open(file_path) as f:
                                    article = json.load(f)
                                    anglicisms_count = 0
                                    total_words_count = 0
                                    anglicisms_count_reduced = 0
                                    total_words_count_reduced = 0
                                    for part in ['title', 'lead', 'body']:
                                        for word in article[part]['lemmatized_text'].split(' '):
                                            total_words_count += 1
                                            if word in anglicisms_list:
                                                anglicisms_count += 1
                                        for word in article[part]['lemmatized_text_reduced'].split(' '):
                                            total_words_count_reduced += 1
                                            if word in anglicisms_list:
                                                anglicisms_count_reduced += 1
                                    anglicisms.append(anglicisms_count / total_words_count)
                                    anglicisms_reduced.append(anglicisms_count_reduced / total_words_count_reduced)
                                    articles_readen += 1
                        except FileNotFoundError:
                            pass
                print()
            anglicisms_mean[year] = (sum(anglicisms) / articles_readen)
            anglicisms_mean_reduced[year] = (sum(anglicisms_reduced) / articles_readen)
    with open('anglicisms_per_year.csv', 'w') as csv_out, open('anglicisms_per_year_reduced.csv', 'w') as csv_reduced:
        for year, anglicism_mean in anglicisms_mean.items():
            print(f'{year};{anglicism_mean}', file=csv_out)
        for year, anglicism_mean_reduced in anglicisms_mean_reduced.items():
            print(f'{year};{anglicism_mean_reduced}', file=csv_reduced)


def get_anglicisms_from_articles_per_province():
    """Generates a CSV which gives the anglicisms usage percentage of all the articles per province"""
    start_cfg_date, end_cfg_date = get_dates_from_cfg()

    anglicisms_mean = {}
    anglicisms_mean_reduced = {}
    with open("anglicisms.txt") as anglicisms_file:
        anglicisms_list = [line.strip() for line in anglicisms_file.readlines()]
        for category in read_categories_from_file():
            print(f'Extracting {category}\'s news...')
            anglicisms = []
            anglicisms_reduced = []
            articles_readen = 0
            for date_between in get_dates_between(start_cfg_date, end_cfg_date):
                print(f'\tExtracting {date_between}\'s news...', end='\r')
                try:
                    current_dir_path = f'{DUMP_DIR}/{category}/{date_between.strftime(DATES_FILE_FORMAT)}'
                    for filename in os.listdir(current_dir_path):
                        file_path = f'{current_dir_path}/{filename}'
                        with open(file_path) as f:
                            article = json.load(f)
                            anglicisms_count = 0
                            total_words_count = 0
                            anglicisms_count_reduced = 0
                            total_words_count_reduced = 0
                            for part in ['title', 'lead', 'body']:
                                for word in article[part]['lemmatized_text'].split(' '):
                                    total_words_count += 1
                                    if word in anglicisms_list:
                                        anglicisms_count += 1
                                for word in article[part]['lemmatized_text_reduced'].split(' '):
                                    total_words_count_reduced += 1
                                    if word in anglicisms_list:
                                        anglicisms_count_reduced += 1
                            anglicisms.append(anglicisms_count / total_words_count)
                            anglicisms_reduced.append(anglicisms_count_reduced / total_words_count_reduced)
                            articles_readen += 1
                except FileNotFoundError:
                    pass
            print()
            anglicisms_mean[category] = (sum(anglicisms) / articles_readen)
            anglicisms_mean_reduced[category] = (sum(anglicisms_reduced) / articles_readen)
    with open('anglicisms_per_province.csv', 'w') as csv_out, \
            open('anglicisms_per_province_reduced.csv', 'w') as csv_reduced:
        for year, anglicism_mean in anglicisms_mean.items():
            print(f'{year};{anglicism_mean}', file=csv_out)
        for year, anglicism_mean_reduced in anglicisms_mean_reduced.items():
            print(f'{year};{anglicism_mean_reduced}', file=csv_reduced)


def get_anglicisms_from_articles_total():
    """Generates a CSV which gives the anglicisms usage percentage of all the articles"""
    start_cfg_date, end_cfg_date = get_dates_from_cfg()

    anglicisms = []
    anglicisms_reduced = []
    articles_readen = 0
    with open("anglicisms.txt") as anglicisms_file:
        anglicisms_list = [line.strip() for line in anglicisms_file.readlines()]
        for category in read_categories_from_file():
            print(f'Extracting {category}\'s news...')
            for date_between in get_dates_between(start_cfg_date, end_cfg_date):
                print(f'\tExtracting {date_between}\'s news...', end='\r')
                try:
                    current_dir_path = f'{DUMP_DIR}/{category}/{date_between.strftime(DATES_FILE_FORMAT)}'
                    for filename in os.listdir(current_dir_path):
                        file_path = f'{current_dir_path}/{filename}'
                        with open(file_path) as f:
                            article = json.load(f)
                            anglicisms_count = 0
                            total_words_count = 0
                            anglicisms_count_reduced = 0
                            total_words_count_reduced = 0
                            for part in ['title', 'lead', 'body']:
                                for word in article[part]['lemmatized_text'].split(' '):
                                    total_words_count += 1
                                    if word in anglicisms_list:
                                        anglicisms_count += 1
                                for word in article[part]['lemmatized_text_reduced'].split(' '):
                                    total_words_count_reduced += 1
                                    if word in anglicisms_list:
                                        anglicisms_count_reduced += 1
                            anglicisms.append(anglicisms_count / total_words_count)
                            anglicisms_reduced.append(anglicisms_count_reduced / total_words_count_reduced)
                            articles_readen += 1
                except FileNotFoundError:
                    pass
            print()
    print('normal: ', sum(anglicisms) / articles_readen)
    print('reduced: ', sum(anglicisms_reduced) / articles_readen)


if __name__ == '__main__':
    # Example:
    get_news_from_topics_with_count(text='lemmatized_text_reduced', csv_suffix='_corrupción',
                                    topics={'corrupción',
                                            'anticorrupción',
                                            'corrupto',
                                            'corruptela',
                                            'trama',
                                            'cochecho',
                                            'soborno',
                                            'imputado',
                                            'blanqueo',
                                            'malversación',
                                            'prevaricación'
                                            },
                                    raw_topics={'falsedad documental',
                                                'financiación ilegal',
                                                'tráfico de influencias',
                                                })
