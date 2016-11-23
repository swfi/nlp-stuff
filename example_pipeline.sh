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
head -1000 ../nlp/wiki.en.text > tmp.txt
python ~/nlp-stuff/train_word2vec.py tmp.txt wiki.en.text.model wiki.en.text.vector

python train_word2vec_model.py wiki.en.text wiki.en.text.model wiki.en.text.vector
python train_word2vec_model.py wiki.sv.text wiki.sv.text.model wiki.sv.text.vector

# Extract vocabularies from the wiktionary dumps (takes about 1 hour:):
python /Users/thowhi/nlp-stuff/extract_wiktionary_titles.py sv_wiktionary_v2.xml titleNames_SwedishWiki_uniq.txt Svenska
python /Users/thowhi/nlp-stuff/extract_wiktionary_titles.py en_wiktionary_v2.xml titleNames_EnglishWiki_uniq.txt English

# Extract vocabularies from the "saldo" and "twelve dicts" resources instead:
awk '$1 ~ /.+\.\.[0-9]/ {print $1}' /Volumes/TomsDisk/Projects/NLP/saldo_2.3/saldo20v03.txt | awk -F '.' '{print $1}' | tr '[:upper:]' '[:lower:]' | awk 'NF == 1' > swedishWords_saldo.txt
cat /Volumes/TomsDisk/Projects/NLP/12dicts-6/American/*.txt /Volumes/TomsDisk/Projects/NLP/12dicts-6/International/*.txt | tr '[:upper:]' '[:lower:]' | sort | uniq | awk 'NF == 1' > englishWords_twelveDicts.txt

# Use the wiktionary words to filter the word2vec matrices:
#titleNames_SwedishWiki_uniq.txt
#titleNames_EnglishWiki_uniq.txt
python /Users/thowhi/nlp-stuff/filter_word2vec_on_vocab.py swedishWords_saldo.txt wiki.sv.text.vector matrix_swedish.txt
python /Users/thowhi/nlp-stuff/filter_word2vec_on_vocab.py englishWords_twelveDicts.txt wiki.en.text.vector matrix_english.txt

# Get the training-word translations:
awk '$1 !~ /^[0-9]+$/ {print $1}' matrix_english.txt | head -6000 > MostCommonEnglishWords_6000.txt
awk '$1 !~ /^[0-9]+$/ {print $1}' matrix_swedish.txt | head -6000 > MostCommonSwedishWords_6000.txt

python /Users/thowhi/nlp-stuff/run_microsoft_translation.py MostCommonSwedishWords_6000.txt sv en EnglishTranslations.txt appName secret
python /Users/thowhi/nlp-stuff/run_microsoft_translation.py MostEnglishSwedishWords_6000.txt en sv SwedishTranslations.txt appName secret

# Obtain English and Swedish word vectors for English->Swedish and Swedish->English word pairings:
python /Users/thowhi/nlp-stuff/retrieve_training_vectors.py EnglishTranslations.txt matrix_swedish.txt matrix_english.txt CommonSwedish_SwedishVectors.txt CommonSwedish_EnglishVectors.txt
python /Users/thowhi/nlp-stuff/retrieve_training_vectors.py SwedishTranslations.txt matrix_english.txt matrix_swedish.txt CommonEnglish_EnglishVectors.txt CommonEnglish_SwedishVectors.txt

# Train a translation matrix to convert Swedish->English, and one to convert English->Swedish:
python /Users/thowhi/nlp-stuff/derive_translation_matrix.py --trainingRate 0.0005 --n-iter 20 --lang1-vectors-filename CommonEnglish_EnglishVectors.txt --lang2-vectors-filename CommonEnglish_SwedishVectors.txt --output-prefix English2Swedish_CommonEnglish

python /Users/thowhi/nlp-stuff/derive_translation_matrix.py --trainingRate 0.0005 --n-iter 20 --lang1-vectors-filename CommonSwedish_EnglishVectors.txt --lang2-vectors-filename CommonSwedish_SwedishVectors.txt --output-prefix English2Swedish_CommonSwedish

python /Users/thowhi/nlp-stuff/derive_translation_matrix.py --trainingRate 0.0005 --n-iter 20 --lang1-vectors-filename CommonEnglish_SwedishVectors.txt --lang2-vectors-filename CommonEnglish_EnglishVectors.txt --output-prefix Swedish2English_CommonEnglish

python /Users/thowhi/nlp-stuff/derive_translation_matrix.py --trainingRate 0.0005 --n-iter 20 --lang1-vectors-filename CommonSwedish_SwedishVectors.txt --lang2-vectors-filename CommonSwedish_EnglishVectors.txt --output-prefix Swedish2English_CommonSwedish

# Translate the english words to the swedish space, and vice-versa:
python /Users/thowhi/nlp-stuff/translate_vectors.py --source-lang-vectors matrix_swedish.txt --translation-matrix Swedish2English_CommonSwedish_TranslationMatrix_0.000500.txt --output-vectors-filename swedish2english_vectors.txt
python /Users/thowhi/nlp-stuff/translate_vectors.py --source-lang-vectors matrix_english.txt --translation-matrix English2Swedish_CommonSwedish_TranslationMatrix_0.000500.txt --output-vectors-filename english2swedish_vectors.txt

# Get the closest 100 words, for each word, for all four possible language comparisons:
python /Users/thowhi/nlp-stuff/get_closest_words.py --lang1-vectors-file matrix_english.txt --lang2-vectors-file matrix_english.txt --output-file closest_words_english2english.json
python /Users/thowhi/nlp-stuff/get_closest_words.py --lang1-vectors-file matrix_swedish.txt --lang2-vectors-file matrix_swedish.txt --output-file closest_words_swedish2swedish.json
python /Users/thowhi/nlp-stuff/get_closest_words.py --lang1-vectors-file matrix_english.txt --lang2-vectors-file swedish2english_vectors.txt --output-file closest_words_swedish2english.json
python /Users/thowhi/nlp-stuff/get_closest_words.py --lang1-vectors-file matrix_swedish.txt --lang2-vectors-file english2swedish_vectors.txt --output-file closest_words_english2swedish.json

# Get closest single word for swedish-english and english-swedish also:
python /Users/thowhi/nlp-stuff/get_closest_words.py --lang1-vectors-file matrix_english.txt --lang2-vectors-file swedish2english_vectors.txt --output-file closest_word_swedish2english.json --num-closest 1
python /Users/thowhi/nlp-stuff/get_closest_words.py --lang1-vectors-file matrix_swedish.txt --lang2-vectors-file english2swedish_vectors.txt --output-file closest_word_english2swedish.json --num-closest 1

python /Users/thowhi/nlp-stuff/calculate_densities.py --lang1-closest-words-file closest_words_english2english.json --lang2-closest-words-file closest_words_swedish2english.json --lang2-closest-word-file closest_word_swedish2english.json --output-file word_densities_english.txt
python /Users/thowhi/nlp-stuff/calculate_densities.py --lang1-closest-words-file closest_words_swedish2swedish.json --lang2-closest-words-file closest_words_english2swedish.json --lang2-closest-word-file closest_word_english2swedish.json --output-file word_densities_swedish.txt

python /Users/thowhi/nlp-stuff/calc_freqs.py matrix_english.txt ../nlp/wiki.en.text word_freqs_english.txt
python /Users/thowhi/nlp-stuff/calc_freqs.py matrix_swedish.txt ../nlp/wiki.sv.text word_freqs_swedish.txt

# Annotate the words with part-of-speech tagging:
cd /Volumes/TomsDisk/Projects/NLP/ReengineeringPipeline
python /Users/thowhi/nlp-stuff/tag_pos.py --word-vectors-file matrix_english.txt --output english_pos.txt
python /Users/thowhi/nlp-stuff/tag_pos.py --word-vectors-file matrix_swedish.txt --output swedish_pos.txt

# Generate a csv file of annotated nodes and a csv file of weighted edges:
python /Users/thowhi/nlp-stuff/collate_word_annotations.py --pos-tags english_pos.txt --nearby-words closest_words_english2english.json --word-freqs word_freqs_english.txt --word-densities word_densities_english.txt --output-nodes nodes_english.csv --output-edges edges_english.csv
python /Users/thowhi/nlp-stuff/collate_word_annotations.py --pos-tags swedish_pos.txt --nearby-words closest_words_swedish2swedish.json --word-freqs word_freqs_swedish.txt --word-densities word_densities_swedish.txt --output-nodes nodes_swedish.csv --output-edges edges_swedish.csv --density-num-top 1000 --min-sim 0.7 --min-freq 0.0001

python /Users/thowhi/nlp-stuff/collate_word_annotations.py --pos-tags english_pos.txt --nearby-words closest_words_english2english.json --word-freqs word_freqs_english.txt --word-densities word_densities_english.txt --output-nodes nodes_english_all.csv --output-edges edges_english_all.csv --density-num-top -1
python /Users/thowhi/nlp-stuff/collate_word_annotations.py --pos-tags swedish_pos.txt --nearby-words closest_words_swedish2swedish.json --word-freqs word_freqs_swedish.txt --word-densities word_densities_swedish.txt --output-nodes nodes_swedish_all.csv --output-edges edges_swedish_all.csv --density-num-top -1 --min-sim 0.7 --min-freq 0.0001


#57211
# XXX continue here. Visualise the swedish and english networks in gephi. Check that the swedish one looks similar to before, and if so, see if the english one has a similar topology.

# Rank words by the density metric, and then generate connected components using that restricted set of nodes:
