# -*- coding: utf-8 -*-
import codecs, logging, pdb, sys
import begin


def split_lines(infile):
    for line in infile.xreadlines():
        yield line.strip().split()


def count_occurrences(tup_dict, line_tok_iter):
    tup_size = len(tup_dict.keys()[0])
    total_word_count = 0
    line_count = 0
    for curr_line_toks in line_tok_iter:
        if line_count % 1000 == 0:
            logging.info("PROGRESS: " + str(line_count))
        tok_idx = 0
        while tok_idx < (len(curr_line_toks) + tup_size):
            curr_toks = map(lambda word: word.decode("utf-8"), curr_line_toks[tok_idx:tok_idx+tup_size])
            curr_tok_tuple = tuple(curr_toks)
            total_word_count += 1
            if tup_dict.has_key(curr_tok_tuple):
                tup_dict[curr_tok_tuple] += 1
            tok_idx += 1
        line_count += 1
    return total_word_count


@begin.start(auto_convert=True)
def calc_freqs(matrix_file="matrix.txt", corpus_file="corpus.txt", output_file="output.txt"):
    # Extract two dictionaries - single words, and word pairs:
    word_counts = {}
    word_pair_counts = {}
    logging.root.setLevel(level=logging.INFO)
    logging.info("Retrieving tuples from matrix file...")
    for line in codecs.open(matrix_file, 'r', encoding="utf_8"):
        elems = line.strip().split()
        if len(elems) > 2:
            tokens = elems[0].split("_")
            if len(tokens) == 1:
                word_counts[tuple(tokens)] = 0
            elif len(tokens) == 2:
                word_pair_counts[tuple(tokens)] = 0

    infile = codecs.open(corpus_file, 'r', encoding="utf_8")
    line_tok_iter = split_lines(infile)
    logging.info("Counting single words...")
    single_word_count = count_occurrences(word_counts, line_tok_iter)

    infile = codecs.open(corpus_file, 'r', encoding="utf_8")
    line_tok_iter = split_lines(infile)
    logging.info("Counting word pairs...")
    paired_word_count = count_occurrences(word_pair_counts, line_tok_iter)

    out_file = codecs.open(output_file, 'w', encoding="utf_8")
    logging.info("Outputting word counts...")
    for word_tup in word_counts.keys():
        print >> out_file, "_".join(word_tup), len(word_tup), (float(word_counts[word_tup])*1000)/single_word_count

    logging.info("Outputting word pair counts...")
    for word_tup in word_pair_counts.keys():
        print >> out_file, "_".join(word_tup), len(word_tup), (float(word_pair_counts[word_tup])*1000)/paired_word_count
