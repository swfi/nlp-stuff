import codecs, cPickle, json, pdb, sys
import numpy as np

from microsofttranslator import Translator

common_lang1_words_filename = sys.argv[1]
lang1_code = sys.argv[2]
lang2_code = sys.argv[3]
output_filename = sys.argv[4]
app_name = sys.argv[5]
app_secret = sys.argv[6]

common_lang1_words = [line.strip() for line in codecs.open(common_lang1_words_filename, encoding="utf_8").readlines()]

lang2_translations = []

translator = Translator(app_name, app_secret)

for startIdx in (np.array(range(int(len(common_lang1_words)/100)))*100):
  print >> sys.stderr, startIdx
  endIdx = startIdx+100
  curr_words = common_lang1_words[startIdx:endIdx]
  try:
    curr_translations = translator.translate_array(curr_words, lang2_code)
    lang2_translations.append(curr_translations)
  except Exception, e:
    print >> sys.stderr, "Failed:", startIdx
    print >> sys.stderr, e
    sys.exit(1)

translated_words = [trans["TranslatedText"] for trans in reduce(lambda list1, list2: list1 + list2, lang2_translations)]

output_file = codecs.open(output_filename, 'w', encoding="utf_8")

# Generate translation pairings, but only for one-to-one word mappings:
for word_idx in range(len(translated_words)):
    translated_word = translated_words[word_idx]
    if len(translated_word.split(" ")) == 1:
        print >> output_file, common_lang1_words[word_idx], translated_word

output_file.close()
