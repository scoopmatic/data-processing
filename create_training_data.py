import json
import sys
import collections
import re


def timediff(prior, latter):
    mins, secs = str(prior).strip().split('.')
    if len(secs) == 1:
        secs += '0'
    prior_secs = int(mins)*60+int(secs)
    mins, secs = str(latter).strip().split('.')
    if len(secs) == 1:
        secs += '0'
    latter_secs = int(mins)*60+int(secs)
    diff = latter_secs - prior_secs
    diff_mins = diff//60
    diff_secs = diff%60
    return "%d.%d" % (diff_mins, diff_secs)


def generate_input(event, context, xml_style=True):
    out = []
    # Define selection and order of information for training input
    if event['Type'] == 'Lopputulos':
        out.append(('type', 'result'))
        out.append(('home', event['Home']))
        out.append(('guest', event['Guest']))
        out.append(('score', event['Score']))
        out.append(('periods', event['Periods']))
        #out.append(('time', event['Time']))
        context['final_score'] = event['Score']
    elif event['Type'] == 'Maali':
        out.append(('type', 'goal'))
        out.append(('score', event['Score']))
        out.append(('team', event['Team']))
        out.append(('player', event['Player']))
        out.append(('assist', event['Assist']))
        out.append(('time', event['Time']))
        if 'time_diff' in event:
            #out.append(('timediff', timediff(context['last_goal_time'], event['Time'])))
            out.append(('timediff', event['time_diff']))
        out.append(('period', int(float(event['Time'])//20+1)))
        goal_types = []
        if 'final_score' in context and event['Score'] == context['final_score']:
            goal_types.append('final')
        if 'deciding_goal' in context and context['deciding_goal'] == event['Score']:
            goal_types.append('deciding')
        if goal_types:
            out.append(('goaltype', ', '.join(goal_types)))
        out.append(('abbrevs', event['Abbreviations']))
        #context['last_goal_time'] = event['Time']
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
        # Unrecognized event type, print everything
        for key in event: # Add any information that might have been left out
            if key in ['event_idx']: # Ignore list
                continue
            if key not in dict(out):
                out.append((key, event[key]))

    if xml_style:
        return ' '.join(['<%s>%s</%s>' % (k,v,k) for k,v in out])
    else:
        return ', '.join(['%s=\'%s\'' % (k,v) for k,v in out])


if len(sys.argv) < 2:
    print("Usage: %s <annotated events JSON meta file>" % sys.argv[0], file=sys.stderr)
    sys.exit()

meta = json.load(open(sys.argv[1]))

event_ref_pat = re.compile("^E\d+$")

for key in meta:
    # Calculate time diff between goals
    last_goal_time = None
    for event in meta[key]['events']:
        if event['Type'] == 'Maali':
            if last_goal_time:
                event['time_diff'] = timediff(last_goal_time, event['Time'])
            last_goal_time = event['Time']

    # Collect events with mentions
    entries = collections.defaultdict(lambda: [])
    for event in meta[key]['events']:
        if 'text' in event:
            #print(event)
            if event_ref_pat.search(event['text']): # Is event reference?
                entries[event['text']].append(event)
            else:
                entries[event['event_idx']].append(event)

    if not entries:
        continue

    print()
    print("GAME:", key)
    context = {}

    # Identify deciding goal
    last_score = None
    loosing_score = None
    for event in meta[key]['events'][::-1]:
        if event['Type'] == 'Maali':
            s1, s2 = event['Score'].split('\u2013')
            s1, s2 = int(s1), int(s2)
            if last_score is None:
                loosing_score = min(s1, s2)
            if loosing_score and max(s1, s2) == loosing_score+1:
                context['deciding_goal'] = event['Score']
            if s1 == s2:
                break
            last_score = event['Score']

    # Print results
    for idx, events in entries.items():
        text = None
        for event in events:
            print('   IN:', generate_input(event, context, xml_style=False))
            if not event_ref_pat.search(event['text']):
                text = event['text']

        print('   OUT:', text)
        print()
