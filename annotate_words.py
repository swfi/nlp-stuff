import codecs, logging, sys
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
        word2tag[tup[0]] = tup[1]

    return word2tag


@begin.start(auto_convert=True)
def annotate_words(lang1_vectors_file = "lang1_vectors.txt", lang2_vectors_file = "lang2_vectors.txt"):
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    logging.info("Loading language 1 word vectors...")
    lang1_vectors = gensim.models.Word2Vec.load_word2vec_format(lang1_vectors_file, binary=False)

    logging.info("Loading language 2 word vectors...")
    lang2_vectors = gensim.models.Word2Vec.load_word2vec_format(lang2_vectors_file, binary=False)

    lang1_words = lang1_vectors.vocab.keys()

    logging.info("Assigning POS tags...")
    lang1_word_tags = tag_words(lang1_words)

    lang1_df = pd.DataFrame.from_dict(lang_word_tags)



    pdb.set_trace()
    dummy = 1
