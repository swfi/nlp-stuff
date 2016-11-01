# -*- coding: utf-8 -*-
import codecs, collections, json, logging, pdb, sys
import begin
import pandas as pd


def generate_edges(nearby_words_file, output_edges_file, words_to_include, min_sim, max_neighbours):
    # Process nearby words file line by line rather than loading into
    # memory, as it can be large:
    print >> output_edges_file, "Source,Target,Weight"
    for line in nearby_words_file.xreadlines():
        elems = line.strip().split()

        # Nasty hack...
        if len(elems) > 1:
            word_dists = json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode("{" + line.strip() + "}")
            word1 = word_dists.keys()[0]
            close_word_dists = word_dists.values()[0]
            filt_words = filter(lambda word: close_word_dists[word] > min_sim,
                                close_word_dists.keys()[1:])
            closest_words = filt_words[:min(max_neighbours, len(filt_words))]
            for word2 in closest_words:
                if word1 in words_to_include and word2 in words_to_include:
                    print >> output_edges_file, word1 + "," + word2 + "," + str(close_word_dists[word2])


@begin.start(auto_convert=True)
def annotate_words(pos_tags="pos_tags.txt", nearby_words="closest_words.json", word_freqs="word_freqs.txt", word_densities="word_densities.txt", output_nodes="nodes.csv", output_edges="edges.csv", min_sim=0.5, max_neighbours=3, min_freq=3E-5):
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    logging.info("Loading pos tags...")
    pos_tags_table = pd.read_table(pos_tags, sep=" ", index_col=0, names=["pos"])

    logging.info("Loading word freqs...")
    word_freqs_table = pd.read_table(word_freqs, sep=" ", index_col=0, names=["freqs"])

    logging.info("Loading word densities...")
    word_dens_table = pd.read_table(word_densities, sep=" ", index_col=0, header=None)

    logging.info("Generating nodes...")

    nodes_table = pd.concat([pos_tags_table, word_freqs_table, word_dens_table], axis=1)
    nodes_table['ID'] = nodes_table.index
    nodes_table['Label'] = nodes_table.index

    nodes_table_filt = nodes_table.loc[nodes_table['freqs'] > min_freq,:]

    nodes_table_filt.to_csv(output_nodes, encoding="utf-8", index=False)

    words_to_include = map(lambda word: str(word).decode("utf8"), nodes_table_filt.ID.to_dict().keys())

    nodes_table_loaded = pd.read_table(output_nodes, encoding="utf-8", sep=",")

    logging.info("Generating edges...")
    nearby_words_file = codecs.open(nearby_words, 'r', encoding="utf_8")
    output_edges_file = codecs.open(output_edges, 'w', encoding="utf_8")
    generate_edges(nearby_words_file, output_edges_file, words_to_include, min_sim, max_neighbours)
    nearby_words_file.close()
