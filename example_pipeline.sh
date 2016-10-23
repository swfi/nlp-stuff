#!/bin/bash

# Retrieve the wikipedia dumps:
curl "https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2" -o "enwiki.xml.bz2"
curl "https://dumps.wikimedia.org/svwiki/latest/svwiki-latest-pages-articles.xml.bz2" -o "svwiki.xml.bz2"

# Retrieve the wiktionary dumps:
curl "https://dumps.wikimedia.org/enwiktionary/20160920/enwiktionary-20160920-pages-articles.xml.bz2" -o "enwiktionary.xml.bz2"
curl "https://dumps.wikimedia.org/svwiktionary/20160920/svwiktionary-20160920-pages-articles.xml.bz2" -o "svwiktionary.xml.bz2"

bzip2 -d enwiktionary.xml.bz2
bzip2 -d svwiktionary.xml.bz2

# Extract cleaned corpuses:
python process_wiki.py enwiki.xml.bz2 wiki.en.text
python process_wiki.py svwiki.xml.bz2 wiki.sv.text

# Train word2vec models:
python train_word2vec_model.py wiki.en.text wiki.en.text.model wiki.en.text.vector
python train_word2vec_model.py wiki.sv.text wiki.sv.text.model wiki.sv.text.vector

# Extract vocabularies from the wiktionary dumps (takes about 1 hour:):
python /Users/thowhi/nlp-stuff/extract_wiktionary_titles.py sv_wiktionary_v2.xml titleNames_SwedishWiki_uniq.txt Svenska
python /Users/thowhi/nlp-stuff/extract_wiktionary_titles.py en_wiktionary_v2.xml titleNames_EnglishWiki_uniq.txt English

# Use the wiktionary words to filter the word2vec matrices:
python /Users/thowhi/nlp-stuff/filter_word2vec_on_vocab.py titleNames_SwedishWiki_uniq.txt wiki.sv.text.vector matrix_swedish.txt
python /Users/thowhi/nlp-stuff/filter_word2vec_on_vocab.py titleNames_EnglishWiki_uniq.txt wiki.en.text.vector matrix_english.txt

# Get the training-word translations:
awk '$1 !~ /^[0-9]+$/ {print $1}' matrix_english.txt | head -6000 > MostCommonEnglishWords_6000.txt
awk '$1 !~ /^[0-9]+$/ {print $1}' matrix_swedish.txt | head -6000 > MostCommonSwedishWords_6000.txt

python /Users/thowhi/nlp-stuff/run_microsoft_translation.py MostCommonSwedishWords_6000.txt sv en EnglishTranslations.txt appName secret
python /Users/thowhi/nlp-stuff/run_microsoft_translation.py MostEnglishSwedishWords_6000.txt en sv SwedishTranslations.txt appName secret

# Obtain English and Swedish word vectors for English->Swedish and Swedish->English word pairings:
python /Users/thowhi/nlp-stuff/retrieve_training_vectors.py EnglishTranslations.txt matrix_swedish.txt matrix_english.txt CommonSwedish_SwedishVectors.txt CommonSwedish_EnglishVectors.txt
python /Users/thowhi/nlp-stuff/retrieve_training_vectors.py SwedishTranslations.txt matrix_english.txt matrix_swedish.txt CommonEnglish_EnglishVectors.txt CommonEnglish_SwedishVectors.txt

# Train a translation matrix to convert Swedish->English, and one to convert English->Swedish:
derive_translation_matrix.py

# Get the closest 100 words for each word:
# XXX

# Calculate density statistics for each word:
# XXX

# Rank words by the density metric, and then generate connected components using that restricted set of nodes:
