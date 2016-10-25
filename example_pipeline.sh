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
python /Users/thowhi/nlp-stuff/derive_translation_matrix.py --trainingRate 0.0005 --n-iter 200 --lang1-vectors-filename CommonEnglish_EnglishVectors.txt --lang2-vectors-filename CommonEnglish_SwedishVectors.txt --output-prefix English2Swedish_CommonEnglish

python /Users/thowhi/nlp-stuff/derive_translation_matrix.py --trainingRate 0.0005 --n-iter 200 --lang1-vectors-filename CommonSwedish_EnglishVectors.txt --lang2-vectors-filename CommonSwedish_SwedishVectors.txt --output-prefix English2Swedish_CommonSwedish

python /Users/thowhi/nlp-stuff/derive_translation_matrix.py --trainingRate 0.0005 --n-iter 200 --lang1-vectors-filename CommonEnglish_SwedishVectors.txt --lang2-vectors-filename CommonEnglish_EnglishVectors.txt --output-prefix Swedish2English_CommonEnglish

python /Users/thowhi/nlp-stuff/derive_translation_matrix.py --trainingRate 0.0005 --n-iter 200 --lang1-vectors-filename CommonSwedish_SwedishVectors.txt --lang2-vectors-filename CommonSwedish_EnglishVectors.txt --output-prefix Swedish2English_CommonSwedish

# Translate the english words to the swedish space, and vice-versa:
python /Users/thowhi/nlp-stuff/translate_vectors.py --source-lang-vectors matrix_swedish.txt --translation-matrix Swedish2English_CommonSwedish_TranslationMatrix_0.000500.txt --output-vectors-filename swedish2english_vectors.txt

python /Users/thowhi/nlp-stuff/translate_vectors.py --source-lang-vectors matrix_english.txt --translation-matrix English2Swedish_CommonSwedish_TranslationMatrix_0.000500.txt --output-vectors-filename english2swedish_vectors.txt

# Get the closest 100 words, for each word, for all four possible language comparisons:
python /Users/thowhi/nlp-stuff/get_closest_words.py --lang1-vectors-file matrix_english.txt --lang2-vectors-file matrix_english.txt --output-file closest_words_english2english.txt
python /Users/thowhi/nlp-stuff/get_closest_words.py --lang1-vectors-file matrix_swedish.txt --lang2-vectors-file matrix_swedish.txt --output-file closest_words_swedish2swedish.txt
python /Users/thowhi/nlp-stuff/get_closest_words.py --lang1-vectors-file matrix_english.txt --lang2-vectors-file swedish2english_vectors.txt --output-file closest_words_swedish2english.txt
python /Users/thowhi/nlp-stuff/get_closest_words.py --lang1-vectors-file matrix_swedish.txt --lang2-vectors-file english2swedish_vectors.txt --output-file closest_words_english2swedish.txt


# Annotate the words with word density statistics, frequency information, and part-of-speech tagging:
python /Users/thowhi/nlp-stuff/annotate_words.py --lang1-vectors-file matrix_english.txt --lang2-vectors-file swedish2english_vectors.txt


# XXX SEEMS TO BE WORKING: NEXT: Implement steps for calculating relative density statistics using the translated and original matrices, and also implement POS tagging. Then, implement final analysis + graph-generation steps.

# Get the closest 100 words for each word:
# XXX

# Calculate density statistics for each word:
# XXX

# Rank words by the density metric, and then generate connected components using that restricted set of nodes:
