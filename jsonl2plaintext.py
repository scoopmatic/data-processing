# Usage: python3 jsonl2plaintext.py --json stt_full_news_archive.jsonl | gzip -c > stt_full_news_archive.txt.gz

import json
import sys

def main(args):

    # returns a dictionary where key: topic-id or timestamp, value: list of articles/statistics (dictonaries) assigned to a topic-id, or timestamp
    with open(args.json, "rt", encoding="utf-8") as f:
        counter = 0
        for i, document in enumerate(f):
            document=document.strip()
            if not document:
                continue
            try:
                data=json.loads(document)
            except json.decoder.JSONDecodeError:
                print("Invalid line:", document, file=sys.stderr)

            counter += 1

            # Add metadata
            print("###C: doc_id =", counter)
            print("###C: zipfilename =", data["zipfile_name"])
            print("###C: filename =", data["file_name"])

            text = data["text"].replace("\n", "\n\n") # paragraph break must be empty line, not just new line.

            print(text)

            if counter%10000==0:
                print("Seen {x} documents".format(x=counter), file=sys.stderr)


if __name__=="__main__":
    import argparse

    argparser = argparse.ArgumentParser(description='')

    argparser.add_argument('--json', type=str, default="/usr/share/ParseBank/STT/general/stt_full_news_archive.jsonl", help='json filename')

    args = argparser.parse_args()

    main(args)

