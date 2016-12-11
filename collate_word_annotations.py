# -*- coding: utf-8 -*-
import codecs, collections, json, logging, pdb, sys
import begin
import networkx as nx
import pandas as pd
import numpy as np


class SynonymCluster:
    def __init__(self, word_pair_list, clust_idx):
        self.word_pairs = word_pair_list
        self.clust_idx = clust_idx

    def get_words(self):
        word1_list = map(lambda tup: tup[0], self.word_pairs)
        word2_list = map(lambda tup: tup[1], self.word_pairs)
        return set(word1_list + word2_list)

    def get_tagged_word(self, word):
        return "%s_%d" % (word, self.clust_idx)

    def get_uniq_translations(self):
        translation_list = map(lambda tup: tup[1], self.lang2_edges)
        return list(set(translation_list))

    # FIXME: Hacky code, but should work:
    def get_tagged_words(self):
        return map(lambda word: self.get_tagged_word(word), self.get_words())

    def get_tagged_translations(self):
        return map(lambda word: self.get_tagged_word(word), self.get_uniq_translations())

    def set_metrics(self, closest_word_lang2):
        self.lang2_edges = []
        for word1 in self.get_words():
            translation_tup = closest_word_lang2[word1].items()[0]
            word2 = translation_tup[0]
            sim = translation_tup[1]
            self.lang2_edges.append((word1, word2, sim))
        self.cosine_sims = map(lambda tup: tup[2], self.lang2_edges)
        self.median_sim = np.median(self.cosine_sims)
        self.max_sim = max(self.cosine_sims)
        self.max_minus_median = self.max_sim - self.median_sim
        #uniq_lang2_words = len(list(set(self.lang2_words)))
        #uniq_lang1_words = len(list(set(self.clust_words)))
        #word_count_ratio = float(uniq_lang1_words)/float(uniq_lang2_words)
        #self.word_count_ratio = word_count_ratio


def cmpClusts(clust1, clust2):
    if clust1.max_minus_median < clust2.max_minus_median:
        return -1
    elif clust1.max_minus_median == clust2.max_minus_median:
        return 0
    else:
        return 1


def extract_clusters(nearby_words_file, words_to_retain, min_sim, closest_word_lang2):
    # Identify clusters, based on word proximity...

    line_idx = 0
    clust_idx = 0
    clusters = []
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

                # Create a new cluster directly from this these word similarities,
                # but only if there was at least one close word observed:
                if len(close_word_dists) > 0:
                    word_sim_tups = map(lambda tup: (word1, tup[0], tup[1]), close_word_dists)
                    syn_clust = SynonymCluster(word_sim_tups, clust_idx)
                    syn_clust.set_metrics(closest_word_lang2)
                    clust_idx += 1
                    clusters.append(syn_clust)

    return clusters


def generate_graph(clusts, nodes_prefix, edges_prefix):
    # Figure out which words are in clusters; these will be output as nodes:
    logging.info("Outputting nodes and edges...")
    output_nodes_file = codecs.open(nodes_prefix + ".csv", 'w', encoding="utf_8")
    output_edges_file = codecs.open(edges_prefix + ".csv", 'w', encoding="utf_8")
    print >> output_nodes_file, "ID,Label,Language,MedianSim,MaxSim,MaxMinusMedian"
    print >> output_edges_file, "Source,Target,Weight,Label,Language"
    node_lines_to_print = set()
    edge_lines_to_print = set()
    clust_idx = 1
    for clust in clusts:
        for word in clust.get_tagged_words():
            curr_line = "%s,%s,%s,%1.3f,%1.3f,%1.3f" % (word, word, "Lang1", clust.median_sim, clust.max_sim, clust.max_minus_median)
            node_lines_to_print.add(curr_line)
        for word in clust.get_tagged_translations():
            curr_line = "%s,%s,%s,%1.3f,%1.3f,%1.3f" % (word, word, "Lang2", clust.median_sim, clust.max_sim, clust.max_minus_median)
            node_lines_to_print.add(curr_line)
        word_pairs = clust.word_pairs
        translation_pairs = clust.lang2_edges
        for word_pair in word_pairs:
            #(clust.get_tagged_word(word_pair[0]), clust.get_tagged_word(word_pair[1]), word_pair[2], word_pair[2], "same")
            curr_line = "%s,%s,%s,%s,%s" % (word_pair[0], word_pair[1], word_pair[2], word_pair[2], "same")
            edge_lines_to_print.add(curr_line)
        for translation_pair in translation_pairs:
            curr_line = "%s,%s,%s,%s,%s" % (clust.get_tagged_word(translation_pair[0]), clust.get_tagged_word(translation_pair[1]), translation_pair[2], translation_pair[2], "different")
            edge_lines_to_print.add(curr_line)
        clust_idx += 1

    for line in node_lines_to_print:
        print >> output_nodes_file, line
    output_nodes_file.close()

    for line in edge_lines_to_print:
        print >> output_edges_file, line
    output_edges_file.close()


@begin.start(auto_convert=True)
def annotate_words(pos_tags="", word_freqs="", nearby_words="closest_words.json", closest_word_other_lang_file = "closest_word_lang2.json", word_densities="word_densities.txt", nodes_prefix="nodes", edges_prefix="edges", min_sim=0.7, max_neighbours=3, min_word_freq=1E-4, min_word_pair_freq=1E-3, density_num_top=1000):
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    logging.info("Loading pos tags...")
    pos_tags_table = None
    if pos_tags != "":
        pos_tags_table = pd.read_table(pos_tags, sep=" ", index_col=0, names=["pos"])

    logging.info("Loading word freqs...")
    word_freqs_table = None
    if word_freqs != "":
        word_freqs_table = pd.read_table(word_freqs, sep=" ", header=None,
                                         index_col=0, names=["nwords", "freqs"])

    # Apply filter on word frequencies:
    filt_words = set(word_freqs_table.loc[(word_freqs_table.iloc[:,1] > min_word_freq) & (word_freqs_table.iloc[:,0] == 1) | \
                                          (word_freqs_table.iloc[:,1] > min_word_pair_freq) & (word_freqs_table.iloc[:,0] == 2)].index)

    logging.info("Loading second language word similarities...")
    closest_word_lang2 = json.load(codecs.open(closest_word_other_lang_file, 'r', encoding="utf_8"))

    # Extract clusters from the resulting filtered nodes, including information
    # about the edges contributing to the cluster:
    nearby_words_file = codecs.open(nearby_words, 'r', encoding="utf_8")
    clusters = extract_clusters(nearby_words_file, filt_words, min_sim, closest_word_lang2)

    # Filter the clusters on density metrics:
    filt_clusts = filter(lambda cluster: len(cluster.get_words()) >= 5 and len(cluster.get_words()) <= 100, clusters)
    filt_clusts.sort(cmpClusts)

    for clust in filt_clusts:
        print clust.median_sim, clust.max_sim, clust.max_minus_median, " ".join(clust.get_words())

    #for clust in filt_clusts:
    #    print " ".join(map(lambda sim: str(sim), clust.cosine_sims))
    #clust.median_sim, clust.max_sim, clust.max_minus_median

    filt_clusts_only_big_max = filter(lambda cluster: cluster.max_sim >= 0.5, filt_clusts)
    clusts_high_diff = filt_clusts[:100]#int(len(filt_clusts)/20.0)
    clusts_low_diff = filt_clusts_only_big_max[-100:]#int(len(filt_clusts)/20.0)

    generate_graph(filt_clusts, nodes_prefix + "_all", edges_prefix + "_all")
    generate_graph(clusts_high_diff, nodes_prefix + "_highDiff", edges_prefix + "_highDiff")
    generate_graph(clusts_low_diff, nodes_prefix + "_lowDiff", edges_prefix + "_lowDiff")
