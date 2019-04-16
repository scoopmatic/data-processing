import sys
import json
import re

if len(sys.argv) < 3:
    print("Usage: %s <events JSON meta file> <events TXT annotations file>" % sys.argv[0], file=sys.stderr)
    sys.exit()

meta = json.load(open(sys.argv[1]))
anno_f = open(sys.argv[2])

event_pat = re.compile("^(E\d+) ")
for line in anno_f:
    if line.startswith("##BEGINNING-OF-GAME##"):
        key, news_idx, stat_idx = None, None, None
        event_texts = {}
        continue
    if line.startswith("# IDX ="):
        key = line.split('=')[1].strip()
        continue
    if line.startswith("# NEWS IDX ="):
        news_idx = line.split('=')[1].strip()
        continue
    if line.startswith("# STATISTICS IDX ="):
        stat_idx = line.split('=')[1].strip()
        continue
    if line.startswith("##END-OF-GAME##"):
        for event in meta[key]['events']:
            if event['event_idx'] in event_texts:
                event['text'] = event_texts[event['event_idx']]
    match = event_pat.search(line)
    if match:
        event_id = match.groups(0)[0]
        event_text = line.split('|||')[1].strip()
        if event_text:
            event_texts[event_id] = event_text

print(json.dumps(meta, indent=2, sort_keys=False))
