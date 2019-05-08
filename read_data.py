import sys
import xml.etree.ElementTree as et
import re

def get_text(element):
    """ Get text within tag and within nested tags """
    if element.tag.split('}')[-1] == 'h3':
        return "\n" # New section (double newline)
    return re.sub("\s+", " ", ((element.text or '') + ''.join(map(get_text, element)) + (element.tail or '')))

def xml2txt(filename):
    """ Extract plain text from paragraphs in XML """
    try:
        tree = et.parse(filename)
    except:
        return None
    root = tree.getroot()
    namespace = root.tag.split('}')[0]+'}'
    body = root.find(namespace+'contentSet')\
                .find(namespace+'inlineXML')\
                .find(namespace+'html')\
                .find(namespace+'body')

    out = ""
    for elem in body:
        if elem.tag.split('}')[-1] == 'p':
            if elem.text:
                text = get_text(elem)
                if len(text) > 0:
                    out += text.strip() + '\n' # New paragraph (single newline)

    return out

if __name__ == "__main__":
    print (xml2txt(sys.argv[1]))
