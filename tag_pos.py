import codecs, json, logging, sys
import begin
import gensim
import pandas as pd
from polyglot.text import Text


def tag_words(words):
    # Nasty hack: Separate the words with a ".":
    blob = ". ".join(words)
    text = Text(blob)
    text.pos_tags

    word2tag = {}
    for tup in text.pos_tags:
        if tup[0] != ".":
            word2tag[tup[0]] = tup[1]

    return word2tag


@begin.start(auto_convert=True)
def tag_pos(word_vectors_file = "word_vectors.txt", output="tags.txt"):
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    # Currently only accepting a word vectors matrix file as input:
    logging.info("Loading word vectors...")
    word_vectors = gensim.models.Word2Vec.load_word2vec_format(word_vectors_file, binary=False)

    words = word_vectors.vocab.keys()
    word2tag = tag_words(words)

    pos_tags_table = pd.DataFrame(pd.Series(word2tag.values()), columns=["POS"])
    pos_tags_table.index=word2tag.keys()

    pos_tags_table.to_csv(output, encoding="utf-8", sep=" ", index=True, header=False)
