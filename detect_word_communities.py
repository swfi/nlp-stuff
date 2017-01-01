# -*- coding: utf-8 -*-
import codecs, collections, json, logging, pdb, os, sys
import begin
import pandas as pd
import numpy as np
from microsofttranslator import Translator


class WordCommunity:
    def __init__(self, words, community_ID, closest_word_lang2):
        self.words = words
        self.community_ID = community_ID
        self.set_metrics(closest_word_lang2)
        self.language = None

    def get_tagged_word(self, word):
        return "%s_%d" % (word, self.community_ID)

    def determine_language(self, translator):
        separate_words = reduce(lambda l1, l2: l1+l2, map(lambda tok: tok.split("_"), self.words))
        self.language = translator.detect_language(" ".join(separate_words))

    def get_uniq_translations(self):
        translation_list = map(lambda tup: tup[1], self.lang2_edges)
        return list(set(translation_list))

    # FIXME: Hacky code, but should work:
    def get_tagged_words(self):
        return map(lambda word: self.get_tagged_word(word), self.words)

    def get_tagged_translations_and_max_sims(self):
        trans2dist = {}
        for tup in self.lang2_edges:
            tagged_word = self.get_tagged_word(tup[1])
            if not trans2dist.has_key(tagged_word):
                trans2dist[tagged_word] = tup[2]
            elif tup[2] > trans2dist[tagged_word]:
                trans2dist[tagged_word] = tup[2]
        return trans2dist.items()

    def get_tagged_translations(self):
        return map(lambda word: self.get_tagged_word(word), self.get_uniq_translations())

    def set_metrics(self, closest_word_lang2):
        self.lang2_edges = []
        for word1 in self.words:
            translation_tup = closest_word_lang2[word1].items()[0]
            word2 = translation_tup[0]
            sim = translation_tup[1]
            self.lang2_edges.append((word1, word2, sim))
        self.cosine_sims = map(lambda tup: tup[2], self.lang2_edges)
        self.median_sim = np.median(self.cosine_sims)
        self.max_sim = max(self.cosine_sims)
        self.max_minus_median = self.max_sim - self.median_sim


def cmpCommunities(community1, community2):
    if community1.median_sim < community2.median_sim:
        return -1
    elif community1.median_sim == community2.median_sim:
        return 0
    else:
        return 1


def extract_links(nearby_words_file, min_sim, words_to_retain):
    id2word = []
    word2id = {}
    links = []
    id_count = 0
    line_idx = 0
    for line in nearby_words_file.xreadlines():
        if line_idx % 1000 == 0:
            logging.info("PROGRESS: Line: " + str(line_idx))
        line_idx += 1
        # Extract all word pairings from this line:

        if len(line.strip().split()) > 1:
            # Obtain dictionary from current json line:
            line_dict = json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode("{" + line.strip() + "}")
            word1 = line_dict.keys()[0]

            if word1 in words_to_retain:
                # Obtain word and similarity:
                word_dists = line_dict.values()[0].items()

                # Apply similarity threshold and filter on words to retain:
                close_word_dists = filter(lambda tup: tup[1] > min_sim and \
                                         tup[1] != 1 and \
                                         tup[0] in words_to_retain,
                                         word_dists)

                # Record links and node IDs for these words...
                if len(close_word_dists) > 0:
                    if not word2id.has_key(word1):
                        word2id[word1] = id_count
                        id2word.append(word1)
                        id_count += 1

                    for tup in close_word_dists:
                        word2 = tup[0]
                        sim = tup[1]
                        if not word2id.has_key(word2):
                            word2id[word2] = id_count
                            id2word.append(word2)
                            id_count += 1
                        links.append((word2id[word1], word2id[word2], sim))

    return (links, id2word)


# FIXME: A bit hacky (should perhaps use something like "snakemake" instead),
# but should work:
def run_infomap(infomap_path, links_filename, trees_dir, links, id2word, closest_word_lang2, min_clust_size=5, max_clust_size=100):
    # Prepare input "links" file:
    links_file = open(links_filename, 'w')
    for link in links:
        print >> links_file, link[0], link[1], link[2]
    links_file.close()

    # Run infomap:
    call_string = " ".join([infomap_path, "-z", "-2", "-u", links_filename, trees_dir])
    call_result = os.system(call_string)

    links_file_prefix = links_filename.split(".")[0]

    # Combine the infomap output with the id2word keys file, to produce the clusters:
    currClustID = -1
    currWords = []
    word_to_communities = {}
    uniq_comms = []
    for line in open(trees_dir + "/" + links_file_prefix + ".tree").xreadlines():
        if line[0] != "#":
            elems = line.strip().split()
            clustID = int(elems[0].split(":")[0])
            nodeID = int(elems[-1])
            word = id2word[nodeID]
            if clustID != currClustID:
                if len(currWords) >= min_clust_size and len(currWords) <= max_clust_size:
                    curr_clust = set(currWords)
                    curr_word_comm = WordCommunity(curr_clust, clustID, closest_word_lang2)
                    uniq_comms.append(curr_word_comm)
                    for clust_word in currWords:
                        if not word_to_communities.has_key(clust_word):
                            word_to_communities[clust_word] = []
                        word_to_communities[clust_word].append(curr_word_comm)
                currWords = []
            currWords.append(word)
            currClustID = clustID

    return (word_to_communities, uniq_comms)


def filter_links(links, id2word, word_to_communities):
    filtered_links = []
    link_idx = 0
    logging.info("Filtering links: " + str(len(links)))
    for link in links:
        retain_link = False
        word1 = id2word[link[0]]
        word2 = id2word[link[1]]
        word1_communities = []
        word2_communities = []
        if word_to_communities.has_key(word1):
            word1_communities = word_to_communities[word1]
        if word_to_communities.has_key(word2):
            word2_communities = word_to_communities[word2]
        community_words = map(lambda comm: comm.words, word1_communities + word2_communities)
        for clust_words in community_words:
            if word1 in clust_words and word2 in clust_words:
                retain_link = True
        if retain_link:
            filtered_links.append(link)

    return map(lambda link: (id2word[link[0]], id2word[link[1]], link[2]), filtered_links)


def write_outputs(filtered_links, word_communities, nodes_prefix, edges_prefix, closest_word_lang2):
    # Write out the nodes:
    logging.info("Outputting nodes and edges...")
    output_nodes_file = codecs.open(nodes_prefix + ".csv", 'w', encoding="utf_8")
    output_edges_file = codecs.open(edges_prefix + ".csv", 'w', encoding="utf_8")
    print >> output_nodes_file, "ID,Label,Language,MaxLang1ClustSim,MedianSim,MaxSim,MaxMinusMedian"
    print >> output_edges_file, "Source,Target,Weight,Label,Language"
    node_lines_to_print = set()
    for curr_word_comm in word_communities:
        for word in curr_word_comm.words:
            curr_line = "%s,%s,%s,%1.3f,%1.3f,%1.3f,%1.3f" % (word, word, "Lang1", 1, curr_word_comm.median_sim, curr_word_comm.max_sim, curr_word_comm.max_minus_median)
            node_lines_to_print.add(curr_line)
        # XXX CONTINUE HERE: DEBUG THE PROBLEM WITH PRINTING OF SWEDISH WORD NODES
        for (word, max_sim) in curr_word_comm.get_tagged_translations_and_max_sims():
            curr_line = "%s,%s,%s,%1.3f,%1.3f,%1.3f,%1.3f" % (word, word, "Lang2", max_sim, curr_word_comm.median_sim, curr_word_comm.max_sim, curr_word_comm.max_minus_median)
            node_lines_to_print.add(curr_line)

    for line in node_lines_to_print:
        print >> output_nodes_file, line
    output_nodes_file.close()

    # Write out edges...
    all_words_of_interest = reduce(lambda words1, words2: words1.union(words2), map(lambda comm: comm.words, word_communities))
    for link in filtered_links:
        word1 = link[0]
        word2 = link[1]
        print >> output_edges_file, "%s,%s,%1.3f,%1.3f,%s" % (word1, word2, link[2], link[2], "Same")

    # Nasty and redundant but whatever:
    for community in word_communities:
        for word in community.words:
            trans_tup = closest_word_lang2[word].items()[0]
            print >> output_edges_file, "%s,%s,%1.3f,%1.3f,%s" % (word, community.get_tagged_word(trans_tup[0]), trans_tup[1], trans_tup[1], "Different")
    output_edges_file.close()


def filt_dict_on_vals(in_dict, vals):
    out_dict = {}
    for key in in_dict.keys():
        val_list = in_dict[key]
        vals_filtered = filter(lambda val: val in vals, val_list)
        if len(vals_filtered) > 0:
            out_dict[key] = vals_filtered
    return out_dict


@begin.start(auto_convert=True)
def detect_word_communities(infomap_path = "/Users/thowhi/externalProgs/Infomap/Infomap", word_sims="closest_words.json", closest_word_other_lang_file = "closest_word_lang2.json", min_sim = 0.5, word_freqs="", min_word_freq=1E-4, min_word_pair_freq=1E-3, links_filename="links.txt", trees_dir="trees", nodes_prefix="nodes", edges_prefix="edges", trans_app = "", trans_key = "", lang1_code="en"):
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    logging.info("Loading word freqs...")
    word_freqs_table = None
    if word_freqs != "":
        word_freqs_table = pd.read_table(word_freqs, sep=" ", header=None,
                                         index_col=0, names=["nwords", "freqs"])

    logging.info("Loading second language word similarities...")
    closest_word_lang2 = json.load(codecs.open(closest_word_other_lang_file, 'r', encoding="utf_8"))

    # Apply filter on word frequencies:
    filt_words = set(word_freqs_table.loc[(word_freqs_table.iloc[:,1] > min_word_freq) & (word_freqs_table.iloc[:,0] == 1) | \
                                          (word_freqs_table.iloc[:,1] > min_word_pair_freq) & (word_freqs_table.iloc[:,0] == 2)].index)

    # Obtain word similarity links, and output a file for inputting to infomap,
    # along with a key file:
    nearby_words_file = codecs.open(word_sims, 'r', encoding="utf_8")
    (links, id2word) = extract_links(nearby_words_file, min_sim, filt_words)

    (word_to_communities, uniq_communities) = run_infomap(infomap_path, links_filename, trees_dir, links, id2word, closest_word_lang2)

    # Filter the clusters to get the top and bottom clusters ranked by median
    # translation score:
    uniq_communities.sort(cmpCommunities)

    translator = Translator(trans_app, trans_key)

    n_top = int(len(uniq_communities)/10.0)
    poor_translation_communities = uniq_communities[:n_top]
    good_translation_communities = uniq_communities[-n_top:]

#    for comm in poor_translation_communities:
#        comm.determine_language(translator)
#    for comm in good_translation_communities:
#        comm.determine_language(translator)

#    poor_translation_communities = filter(lambda comm: comm.language == lang1_code, poor_translation_communities)
#    good_translation_communities = filter(lambda comm: comm.language == lang1_code, good_translation_communities)

    out_f = open("word_communities_all_" + lang1_code + ".txt", 'w')
    for community in uniq_communities:
        print >> out_f, community.median_sim, " ".join(community.words)
    out_f.close()

    out_f = open("word_communities_poor_translations_" + lang1_code + ".txt", 'w')
    for community in poor_translation_communities:
        print >> out_f, community.median_sim, " ".join(community.words)
    out_f.close()

    out_f = open("word_communities_good_translations_" + lang1_code + ".txt", 'w')
    for community in good_translation_communities:
        print >> out_f, community.median_sim, " ".join(community.words)
    out_f.close()

    word_to_comm_poor = filt_dict_on_vals(word_to_communities, poor_translation_communities)
    word_to_comm_good = filt_dict_on_vals(word_to_communities, good_translation_communities)

    # Filter the edges to only retain those that co-occur in a given word
    # community:
    filtered_links_all = filter_links(links, id2word, word_to_communities)
    filtered_links_poor = filter_links(links, id2word, word_to_comm_poor)
    filtered_links_good = filter_links(links, id2word, word_to_comm_good)

    write_outputs(filtered_links_all, uniq_communities, nodes_prefix + "_" + lang1_code + "_all", edges_prefix + "_all", closest_word_lang2)
    write_outputs(filtered_links_poor, poor_translation_communities, nodes_prefix + "_" + lang1_code + "_poor_translatability", edges_prefix + "_" + lang1_code + "_poor_translatability", closest_word_lang2)
    write_outputs(filtered_links_good, good_translation_communities, nodes_prefix + "_" + lang1_code + "_good_translatability", edges_prefix + "_" + lang1_code + "_good_translatability", closest_word_lang2)
