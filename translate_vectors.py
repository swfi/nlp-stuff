import codecs, pdb
import begin
import gensim
import pandas as pd

@begin.start(auto_convert=True)
def translate(source_lang_vectors = "source_lang_vectors.txt", translation_matrix = "translation_matrix.txt", output_vectors_filename = "translated_vectors.txt"):
    W = pd.read_table(translation_matrix, sep=" ", index_col=0)
    source_vectors = gensim.models.Word2Vec.load_word2vec_format(source_lang_vectors, binary=False)
    vocab_size = len(source_vectors.vocab)
    out_vec_len = len(W.columns)
    outfile = codecs.open(output_vectors_filename, 'w', encoding="utf_8")
    print >> outfile, vocab_size, out_vec_len
    for word in source_vectors.vocab.keys():
        vec = source_vectors[word]
        translated_vec = W.dot(vec)
        print >> outfile, word + " " + " ".join(map(lambda val: str(val), translated_vec))
    outfile.close()
