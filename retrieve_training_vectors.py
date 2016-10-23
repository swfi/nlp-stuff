import pdb, sys
import gensim

word_pairs_file = sys.argv[1]
vectors_lang1_file = sys.argv[2]
vectors_lang2_file = sys.argv[3]
output_matrix_lang1 = open(sys.argv[4], 'w')
output_matrix_lang2 = open(sys.argv[5], 'w')

print >> sys.stderr, "Loading lang1..."
vectors_lang1 = gensim.models.Word2Vec.load_word2vec_format(vectors_lang1_file, binary=False)
print >> sys.stderr, "Loading lang2..."
vectors_lang2 = gensim.models.Word2Vec.load_word2vec_format(vectors_lang2_file, binary=False)

print >> sys.stderr, "Retrieving words..."
for word_pair in [line.strip().split() for line in open(word_pairs_file).readlines()]:
    lang1_word = word_pair[0].decode("utf-8").lower()
    lang2_word = word_pair[1].decode("utf-8").lower()
    try:
        vec1 = vectors_lang1[lang1_word]
        vec2 = vectors_lang2[lang2_word]
    except Exception, e:
        print >> sys.stderr, "FAILED:", lang1_word, lang2_word
        dummy = 1
    print >> output_matrix_lang1, " ".join(map(lambda item: str(item), vec1))
    print >> output_matrix_lang2, " ".join(map(lambda item: str(item), vec1))

output_matrix_lang1.close()
output_matrix_lang2.close()
