#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os.path
import pdb, sys
import multiprocessing

from gensim.corpora import WikiCorpus
from gensim.models import Word2Vec
from gensim.models.word2vec import LineSentence
from gensim.models.phrases import Phrases


def split_input(lines_iterator):
    for line in lines_iterator:
        yield line.strip().split()


if __name__ == '__main__':
    program = os.path.basename(sys.argv[0])
    logger = logging.getLogger(program)

    logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
    logging.root.setLevel(level=logging.INFO)
    logger.info("running %s" % ' '.join(sys.argv))

    inp, outp1, outp2 = sys.argv[1:4]

    wiki_article_lists = split_input(open(inp).xreadlines())
    wiki_articles = LineSentence(inp)
    bigram_transformer = Phrases(wiki_articles)
    model = Word2Vec(bigram_transformer[wiki_articles], size=400, window=5, min_count=5, workers=multiprocessing.cpu_count()-1)

#    model = Word2Vec(LineSentence(inp), size=400, window=5, min_count=5,
#                     workers=multiprocessing.cpu_count()-1)

    # trim unneeded model memory = use(much) less RAM
    #model.init_sims(replace=True)
    model.save(outp1)
    model.save_word2vec_format(outp2, binary=False)
