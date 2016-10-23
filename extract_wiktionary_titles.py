# -*- coding: utf-8 -*-
import codecs, pdb, re, sys
import xml.etree.ElementTree as etree
idx = 0
titleNames = set()
for event, elem in etree.iterparse(sys.argv[1], events=('start', 'end', 'start-ns', 'end-ns')):
    if idx % 100000 == 0:
        print >> sys.stderr, idx
    idx += 1
    if elem.tag == "page":
        try:
            titleText = elem.findall('title')[0].text
            textText = elem.findall('revision')[0].findall("text")[0].text
            if re.search("==" + sys.argv[3] + "==", textText) != None:
                titleNames.add(titleText)
        except Exception, e:
            pass
    elem.clear()

outF = codecs.open(sys.argv[2], 'w', "utf-8")
titleNamesList = list(titleNames)
titleNamesList.sort()
for titleName in titleNamesList:
    print >> outF, titleName
