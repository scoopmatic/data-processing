import json
import sys

def generate_input(event):
    out = []
    if event['Type'] == 'Lopputulos':
        out.append(('type', 'result'))
        out.append(('home', event['Home']))
        out.append(('guest', event['Guest']))
        out.append(('score', event['Score']))
        out.append(('periods', event['Periods']))
        out.append(('time', event['Time']))
    elif event['Type'] == 'Maali':
        out.append(('type', 'goal'))
        out.append(('score', event['Score']))
        out.append(('team', event['Team']))
        out.append(('player', event['Player']))
        out.append(('assist', event['Assist']))
        out.append(('time', event['Time']))
        ## TODO:
        #out.append(('timediff', event['Time']))
        #out.append(('period', event['Time']))
        #out.append(('goaltype', event['Time']))
        out.append(('abbrevs', event['Abbreviations']))
    elif event['Type'] == 'J\u00e4\u00e4hy':
        out.append(('type', 'penalty'))
        out.append(('team', event['Team']))
        out.append(('player', event['Player']))
        out.append(('minutes', event['Minutes']))
        out.append(('time', event['Time']))
    elif event['Type'] == 'Torjunnat':
        out.append(('type', 'save'))
        out.append(('team', event['Team']))
        out.append(('player', event['Player']))
        out.append(('saves', event['Saves']))
        out.append(('time', event['Time']))
    else:
        pass
    """for key in event: # Add any information that might have been left out
        if key in ['event_idx']: # Ignore list
            continue
        if key not in dict(out):
            out.append((key, event[key]))"""

    return ' '.join(['<%s>%s</%s>' % (k,v,k) for k,v in out])


if len(sys.argv) < 2:
    print("Usage: %s <annotated events JSON meta file>" % sys.argv[0], file=sys.stderr)
    sys.exit()

meta = json.load(open(sys.argv[1]))

for key in meta:
    for event in meta[key]['events']:
        if 'text' in event:
            print(key)
            print('IN:', generate_input(event))
            print('OUT:', event['text'])
