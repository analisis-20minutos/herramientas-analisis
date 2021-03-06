"""
Pavel Razgovorov (pr18@alu.ua.es), Universidad de Alicante (https://www.ua.es)

Script to clean the stopword entries of a CSV generated by one of the existing scripts in news_stats.py
"""
import csv
import getopt
import sys


def remove_stopwords_from_csv(input_filename, output_filename, delimiter=';', column_name='word'):
    with open('stopwords-es.txt') as stopwords_file, \
            open(input_filename) as csv_in, \
            open(output_filename, 'w') as csv_out:
        stopwords = [line.strip() for line in stopwords_file.readlines()]
        reader = csv.DictReader(csv_in, delimiter=delimiter)
        writer = csv.DictWriter(csv_out, delimiter=delimiter, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows([line for line in reader if line[column_name] and line[column_name] not in stopwords])


if __name__ == '__main__':
    usage = f'usage: {sys.argv[0]} -i <inputfile> -o <outputfile> [-d <delimiter> -c col_name]'
    [inputfile, outputfile, delim, col_name] = [None, None, ';', 'word']
    if len(sys.argv) < 2:
        print(usage)
        exit(2)
    try:
        opts, _ = getopt.getopt(sys.argv[1:], 'hi:o:d:c:', ['help', 'input_file=', 'output_file=', 'delimiter=',
                                                            'col_name='])
    except getopt.GetoptError:
        print(usage)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(usage)
            sys.exit()
        elif opt in ('-i', '--input_file'):
            inputfile = arg
        elif opt in ('-o', '--output_file'):
            outputfile = arg
        elif opt in ('-d', '--delimiter'):
            delim = arg
        elif opt in ('-c', '--col_name'):
            col_name = arg
    if not inputfile or not outputfile:
        print('error: input and output filenames are required')
        print(usage)
        sys.exit(2)
    remove_stopwords_from_csv(inputfile, outputfile, delim, col_name)
