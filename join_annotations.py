import sys
import json
import re
import collections

if len(sys.argv) < 4:
    print("Usage: %s <events JSON meta file> <events TXT annotations file> <JSON output file>" % sys.argv[0], file=sys.stderr)
    sys.exit()

meta = json.load(open(sys.argv[1]))
anno_f = open(sys.argv[2])

INCLUDE_UNALIGNED = False #True
cnt_game_begs, cnt_game_ends, cnt_events = 0, 0, 0
cnt_games_with_text, cnt_events_with_text, cnt_events_without_text = 0, 0, 0
cnt_events_in_nonempty_game = 0
cnt_events_in_game = 0
cnt_event_types = collections.defaultdict(lambda: 0)
PATIENCE = 100
patience_left = PATIENCE
event_pat = re.compile("^(E\d+) ")
event_pat_empty = re.compile("\|\|\|$")

event_texts = {}
for i, line in enumerate(anno_f):
    if line.startswith("##BEGINNING-OF-GAME##"):
        key, news_idx, stat_idx = None, None, None
        #assert event_texts == {}
        event_texts = {}
        cnt_game_begs += 1
        cnt_events_in_game = 0

    elif line.startswith("# IDX ="):
        key = line.split('=')[1].strip()

    elif line.startswith("# NEWS IDX ="):
        news_idx = line.split('=')[1].strip()

    elif line.startswith("# STATICTICS IDX ="): #SIC!
        stat_idx = line.split('=')[1].strip()

    elif line.startswith("##END-OF-GAME##"):
        cnt_game_ends += 1
        game_has_text = False

        if key not in meta: # Game is not in JSON, skip
            continue

        for ei, event in enumerate(meta[key]['events']):
            if event['event_idx'] in event_texts:
                cnt_event_types[event['Type']] += 1
                game_has_text = True
                event['text'] = event_texts[event['event_idx']]
                #meta[key]['events'][ei]['text'] = event_texts[event['event_idx']]
                assert 'text' in meta[key]['events'][ei]
                #event_texts = {}
        if game_has_text:
            cnt_games_with_text += 1
            cnt_events_in_nonempty_game += cnt_events_in_game

        cnt_events_in_game = 0
        if patience_left <= 0:
            print("Empty event annotations: patience elapsed at line", i, file=sys.stderr)
            break
    else:
        match = event_pat.search(line)
        if match:
            cnt_events_in_game += 1
            cnt_events += 1
            if event_pat_empty.search(line):
                cnt_events_without_text += 1
            #cnt_event_types[line.split()[1]] += 1
            event_id = match.groups(0)[0]
            try:
                event_text = line.split('|||')[1].strip()
            except IndexError:
                print("Parse error on line %d in %s: %s" % (i, sys.argv[2], line), file=sys.stderr)
                raise
            if event_text or INCLUDE_UNALIGNED:
                cnt_events_with_text += 1
                event_texts[event_id] = event_text
                patience_left = PATIENCE
            else:
                patience_left -= 1



json.dump(meta, open(sys.argv[3], 'w'), indent=2, sort_keys=False)
print("Found %d (%d) games, %d events" % (cnt_game_begs, cnt_game_ends, cnt_events))
print("Text in %d games, %d events. Not in %d events (%d+%d=%d~%d)" % (cnt_games_with_text, cnt_events_with_text, cnt_events_without_text, cnt_events_without_text, cnt_events_with_text, cnt_events_without_text+cnt_events_with_text, cnt_events))
for evtype in cnt_event_types:
    print("  ", cnt_event_types[evtype], evtype)

print("cnt_events_in_nonempty_game",cnt_events_in_nonempty_game)
