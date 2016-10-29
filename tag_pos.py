import codecs, json, logging, sys
import begin
import gensim
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
def tag_pos(word_vectors_file = "word_vectors.txt", output="tags.json"):
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    # Currently only accepting a word vectors matrix file as input:
    logging.info("Loading word vectors...")
    word_vectors = gensim.models.Word2Vec.load_word2vec_format(word_vectors_file, binary=False)

    words = word_vectors.vocab.keys()
    word2tag = tag_words(words)

    outfile = codecs.open(output, 'w', encoding="utf_8")
    json.dump(word2tag, outfile, indent=4)
    outfile.close()
