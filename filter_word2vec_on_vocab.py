import codecs, pdb, sys
words = set([line.strip().split()[0].split(".")[0].lower() for line in codecs.open(sys.argv[1], "r", "utf-8").readlines() if line[0] != "#"])

matrix_file = codecs.open(sys.argv[2], "r", "utf-8")

tmp_out_file = codecs.open("/tmp/vectors.tmp", 'w', "utf-8")
n_included_words = 0
vec_length = 0
for line in matrix_file.xreadlines():
    if len(line) != 2:
        elems = line.strip().split()
        vec_length = len(elems) - 1
        word = elems[0]
        if word.decode("utf-8") in words:
            n_included_words += 1
            print >> tmp_out_file, line.strip().decode("utf-8")

tmp_out_file.close()

out_file = codecs.open(sys.argv[3], 'w', "utf-8")
print >> out_file, n_included_words, vec_length
for line in open("/tmp/vectors.tmp").xreadlines():
    print >> out_file, line.strip().decode("utf-8")

out_file.close()
