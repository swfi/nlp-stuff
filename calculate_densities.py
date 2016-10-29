import collections, codecs, json, logging, pdb, sys
import begin
import numpy as np
import pandas as pd


def calc_median_ratio_dist(ordered_word_dists1, ordered_word_dists2):
    scores1 = ordered_word_dists1.values()
    scores2 = ordered_word_dists2.values()
    return np.median(scores1)/np.median(scores2)


def calc_neighbour_comparison(word, ordered_word_dists1, lang2_closest_word_dict, operator, neighbourhood=5):
    closest_lang2_dist = lang2_closest_word_dict[word].values()[0]
    five_closest = ordered_word_dists1[word].keys()[1:1+neighbourhood]
    five_closest_lang2_dists = map(lambda curr_word: lang2_closest_word_dict[curr_word].values()[0], five_closest)

    return operator(closest_lang2_dist, np.mean(five_closest_lang2_dists))


@begin.start(auto_convert=True)
def calculate_densities(lang1_closest_words_filename = "lang1_closest_words.json", lang2_closest_words_filename = "lang2_closest_words.json", lang2_closest_word_filename = "lang2_closest_word.json", output_filename = "word_densities.txt"):
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    # I wanted to use some kind of streaming json parser (ijson??) to process
    # the json files, but this does not seem to be straightforward. Just
    # implementing my own parsing rather than spending time on that...

    logging.info("Loading language 1 word vectors...")
    lang1_closest_words_file = codecs.open(lang1_closest_words_filename, "r", "utf-8")
    lang2_closest_words_file = codecs.open(lang2_closest_words_filename, "r", "utf-8")

    output_file = codecs.open(output_filename, "w", "utf-8")

    lang2_closest_word_dict = json.load(codecs.open(lang2_closest_word_filename, "r", "utf-8"))

    curr_line_lang1 = lang1_closest_words_file.readline()
    curr_line_lang2 = lang2_closest_words_file.readline()
    while curr_line_lang1 != "":
        elems_lang1 = curr_line_lang1.strip().split(" ")
        elems_lang2 = curr_line_lang2.strip().split(" ")
        if len(elems_lang1) > 1:
            word_dists_lang1 = json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode("{" + curr_line_lang1.strip() + "}")
            word_dists_lang2 = json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode("{" + curr_line_lang2.strip() + "}")

            word = word_dists_lang1.keys()[0]
            assert word == word_dists_lang2.keys()[0]

            median_dist_ratio = calc_median_ratio_dist(word_dists_lang1[word], word_dists_lang2[word])

            neighbour_comparison_dist_ratio = calc_neighbour_comparison(word, word_dists_lang1, lang2_closest_word_dict,
                                                                        lambda d1, d2: d1/d2)
            neighbour_comparison_dist_diff = calc_neighbour_comparison(word, word_dists_lang1, lang2_closest_word_dict,
                                                                       lambda d1, d2: d1-d2)

            print >> output_file, word, median_dist_ratio, neighbour_comparison_dist_ratio, neighbour_comparison_dist_diff

        curr_line_lang1 = lang1_closest_words_file.readline()
        curr_line_lang2 = lang2_closest_words_file.readline()

    assert curr_line_lang2 == ""
