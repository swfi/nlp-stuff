import codecs, json, logging, pdb, sys
import begin
import gensim


@begin.start(auto_convert=True)
def get_closest_words(lang1_vectors_file = "lang1_vectors.txt", lang2_vectors_file = "lang2_vectors.txt", output_filename = "closest_words.txt", num_closest=100):
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    logging.info("Loading language 1 word vectors...")
    lang1_vectors = gensim.models.Word2Vec.load_word2vec_format(lang1_vectors_file, binary=False)

    logging.info("Loading language 2 word vectors...")
    lang2_vectors = gensim.models.Word2Vec.load_word2vec_format(lang2_vectors_file, binary=False)

    lang1_words = lang1_vectors.vocab.keys()

    # Quick hacky approach for outputting json format without using a huge
    # amount of memory:
    first_line = True
    output_file = codecs.open(output_filename, 'w', encoding="utf_8")
    print >> output_file, "{"
    for query_word in lang1_vectors.vocab.keys():
        vec = lang1_vectors[query_word]
        word2sim = {word: sim for (word, sim) in lang2_vectors.similar_by_vector(vec, topn=num_closest)}
        similarity_string = json.dumps(word2sim)
        if not first_line:
            print >> output_file, ","
        print >> output_file, "\"" + query_word + "\": " + similarity_string
        first_line = False
    print >> output_file, "}"
