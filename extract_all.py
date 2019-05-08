# python extract_all.py /home/mikkos/arkistosiirto* > stt_full_news_archive.jsonl

import sys
import os
import read_data
import argparse
import zipfile
import xml.etree.ElementTree as et
import io
import re
import traceback
import json

def get_text(element):
    """ Get text within tag and within nested tags """
    if element.tag.split('}')[-1] == 'h3':
        return "\n" # New section (double newline)
    return re.sub("\s+", " ", ((element.text or '') + ''.join(map(get_text, element)) + (element.tail or '')))

def xml2txt(root):
    """ Extract plain text from paragraphs in XML """
    namespace = ""#root.tag.split('}')[0]+'}'
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

parser = argparse.ArgumentParser(description='')
parser.add_argument('zipfiles', nargs='+', help='arkistosiirto zipfiles')
args = parser.parse_args()

counter=0
for zipfile_name in args.zipfiles:
    with zipfile.ZipFile(zipfile_name,"r") as open_zip:
        for zip_info in open_zip.infolist():
            if zip_info.filename.endswith(".xml"):
                counter+=1
                contents=open_zip.read(zip_info).decode("utf-8")
                contents=re.sub(' xmlns="[^"]+"', '', contents, count=1)
                try:
                    et_node=et.parse(io.StringIO(contents)).getroot()
                except:
                    print("Something weird in", zip_info.filename,file=sys.stderr,flush=True)
                    traceback.print_exc()
                    print("Skipping...")
                    continue
                timestamp=et_node.find("./itemMeta/firstCreated").text
                stt_topics=[]
                section_names=[]
                for subj_node in et_node.findall("./contentMeta/subject"):
                    if subj_node.attrib["qcode"].startswith("stt-topics:"):
                        stt_topics.append(subj_node.attrib["qcode"])
                        continue
                    for name_node in subj_node.findall("./name"):
                        section_names.append(name_node.text)
                text = xml2txt(et_node)
                assert len(stt_topics)<=1
                if stt_topics:
                    tid=stt_topics[0]
                else:
                    tid=None
                out_dict={"timestamp":timestamp,"topic-id":tid,"sections":section_names,"text":text,"file_name":os.path.basename(zip_info.filename),"zipfile_name":zipfile_name}
                print(json.dumps(out_dict))
                if counter%10000==0:
                    print("...processed",counter,"files",file=sys.stderr,flush=True)
                
