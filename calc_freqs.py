# -*- coding: utf-8 -*-
import codecs, pdb, sys

wordCounts = {}
for line in codecs.open(sys.argv[1], 'r', encoding="utf_8"):
    elems = line.strip().split()
    if len(elems) > 2:
        wordCounts[elems[0]] = 0


lineCount = 0
totalWordCount = 0
for line in codecs.open(sys.argv[2], 'r', encoding="utf_8").xreadlines():
    if lineCount % 1000 == 0:
        print >> sys.stderr, lineCount
    elems = line.strip().split()
    for word in elems:
        if wordCounts.has_key(word.decode("utf-8")):
            wordCounts[word.decode("utf-8")] += 1
            totalWordCount += 1
    lineCount += 1


out_file = codecs.open(sys.argv[3], 'w', encoding="utf_8")
for word in wordCounts.keys():
    print >> out_file, word, (float(wordCounts[word])*1000)/totalWordCount
