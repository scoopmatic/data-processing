import json
import re
import sys
from collections import OrderedDict, Counter

example="""
Kärpät–Ässät 5–2 (0–1, 3–0, 2–1)
1. erä: 12.27 Sami Lähteenmäki (Severi Sillanpää–Dragan Umicevic) 0–1 yv.
Jäähyt: 7.25 Jyri Marttinen Ä 2 min, 9.00 Ville Pokka K 2 min, 11.54 Ari Vallin K 2 min, 18.03 Henri Heino Ä 2 min, 19.01 Ziga Jeglic Ä 2 min.
2. erä: 27.24 Julius Junttila 1–1 sr, 32.15 Mika Pyörälä (Toni Kähkönen–Jari Viuhkola) 2–1, 38.46 Lasse Kukkonen (Viuhkola–Pokka) 3–1 yv.
Jäähyt: 35.53 Sillanpää Ä 2+2 min.
3. erä: 44.31 Simon Suoranta (Joonas Donskoi) 4–1, 51.10 Pyörälä (Viuhkola–Kähkönen) 5–1, 57.46 Sillanpää (Sami Mutanen) 5–2.
Jäähyt: 46.51 Lähteenmäki Ä 2 min, 51.59 Vladimir Eminger K 2 min.
Jäähyt yhteensä: Kärpät 3x2 min=6 min, Ässät 6x2 min=12 min.
Torjunnat: Jussi Rynnäs K 12+7+8=27, Rasmus Rinne Ä 12+8+12=32.
Tuomarit: Jukka Hakkarainen–Mikko Vanninen (Samuli Orava–Harri Perämäki).
Yleisöä 5 014.

4. erä: Maaliton.
Jäähyt: 4.46 Jani Tuppurainen JYP 2 min.
Vl-maali: Janne Keränen 3–2.

"""

abbreviations = ['yv2', 'av2', 'yv', 'av', 'tv', 'sr', 'tm', 'im', 'vl', 'rl', 'vom', 'vt', 'ja']


endresult_regex = re.compile("\([0-9]+(\u2013|-|—)[0-9]+(,|\s)\s?[0-9]+(\u2013|-|—)[0-9]+(,|\s)\s?[0-9]+(\u2013|-|—)[0-9]+", re.UNICODE) # line should have at least (1–1, 1–1, 1–0
score_regex = re.compile("(?=(ja|vl|rl|je)?\.?\s?([0-9]+(?:\u2013|-)[0-9]+))", re.IGNORECASE)

period_regex = re.compile("([1-9]\. erä)|Jatkoaika|Jatkoerä|Vom-kilpailu|Vl-maali", re.IGNORECASE)
abbr_regex = re.compile("(?=("+'|'.join(abbreviations)+"))", re.IGNORECASE)
player_regex = re.compile("[^\(\)0-9]+", re.UNICODE)

goal_regex = re.compile("([0-9]+\.[0-9]+)\.?\s([^\(\)0-9]+)\s(\([^\(\)0-9]+\)\s)?([0-9]+(?:–|-)[0-9]+)(?:\s)?("+"|".join(abbreviations)+")?\.?\s?("+"|".join(abbreviations)+")?\.?\s?("+"|".join(abbreviations)+")?", re.IGNORECASE)
vl_goal_regex = re.compile("Vl-maali\:?\s([^\(\)0-9]+)\s([0-9]+(?:–|-)[0-9]+)", re.IGNORECASE) # Vl-maali: Tapio Laakso 3–2.

penalty_regex = re.compile("([0-9]+\.[0-9]+)\.?\s([^\(\)0-9]+(?:\s[^\(\)0-9]+)?)\s(?:\([^\(\)]+\)\s)?([^\(\)0-9]{1,4})\s([0-9\+]+)\smin", re.IGNORECASE)
save_regex = re.compile("[:,]\s((?:[^\(\)0-9]+\s)?[^\(\)0-9]+)\s([^\(\)0-9]+)\s(?:[0-9\+\(\)]+)=([0-9]+)", re.IGNORECASE)


def extract_endresult(line, teams_regex):
    """  """
    if not endresult_regex.search(line):
        return None, None, []
    teams = re.findall(teams_regex, line)
    if len(teams) != 2:
        print("Something weird in this line:", line, teams, file=sys.stderr)
        return None, None, []
    home, guest = teams
    abbr, score = re.findall(score_regex, line)[0]
    if abbr == "":
        abbr = "noabbr"
    e = OrderedDict()
    e["Type"] = "lopputulos"
    e["Home"] = home
    e["Guest"] = guest
    e["Score"] = score
    e["Abbreviations"] = [abbr]
    e["Time"] = 0.0
    return home, guest, [e]



def infer_team(score, current, home, guest):
    """ Count which team did the goal (home or guest), return a team and current score """
    h, g = re.split("[\u2013–-]", score, maxsplit=1)
    if int(h) > current[0]:
        team = home
    elif int(g) > current[1]:
        team = guest
    else:
        # this is likely an error in the data (one goal reported twice)
        return None, current
    current = (int(h), int(g))
    return team, current


def goal_event(time, player, assist, score, abbr, abbr2, abbr3, team):

    abbrs = [a for a in [abbr, abbr2, abbr3] if a!=""]
    if not abbrs:
        abbrs = ["noabbr"]
    assist_splitter="\u2013"
    if assist_splitter not in assist and assist.count(" ")>1: # heuristic to decide whether "-" is splitting assistants or first names
        assist_splitter = "-"

    e = OrderedDict()
    e["Type"] = "maali"
    e["Score"] = score
    e["Team"] = team
    e["Player"] = player
    e["Assist"] = assist.strip().replace("(", "").replace(")", "").split(assist_splitter)
    e["Abbreviations"] = abbrs
    e["Time"] = float(time) 
    return e

def extract_goals(line, current_score, home, guest):

    if not period_regex.search(line):
        return [], current_score

    goals=goal_regex.findall(line)
    if not goals: 
        if vl_goal_regex.findall(line): # missing time, so normal regex does not catch it, can be jatkoaika-/voittolaukausmaali
            player, score = vl_goal_regex.findall(line)[0]
            team, current_score = infer_team(score, current_score, home, guest)
            if not team:
                current_score, []
            e = goal_event("65.00", player, "", score, "vl", None, None, team)
            return [e], current_score
        return [], current_score # no goals

    events = []
    for goal in goals:
        time, player, assist, score, abbr, abbr2, abbr3 = goal # 6.20, Luttinen, (Nathan Robinson–Petri Lammassaari), 2–0, yv, None, None
        team, current_score = infer_team(score, current_score, home, guest)
        if not team:
            continue # most likely error in the statistics (one goal reported twice)
        events.append(goal_event(time, player, assist, score, abbr, abbr2, abbr3, team))
    return events, current_score


def full_team_name(team_abbr, home, guest):

    if home.lower().startswith(team_abbr.lower()):
        return home
    elif guest.lower().startswith(team_abbr.lower()):
        return guest
    else:
        return team_abbr


def extract_penalties(line, home, guest):

    if not line.startswith("Jäähyt"):
        return []

    penalties=penalty_regex.findall(line)
    if not penalties:
        return [] 

    events = []
    for penalty in penalties:
        time, player, team_abbr, minutes = penalty # 7.25 Jyri Marttinen Ä 2 min

        e = OrderedDict()
        e["Type"] = "jäähy"
        e["Player"] = player
        e["Team"] = full_team_name(team_abbr, home, guest)
        e["Minutes"] = minutes
        e["Time"] = float(time) 
        events.append(e)
    return events


def extract_saves(line, home, guest):

    if not "Torjunnat:" in line:
        return []

    saves=save_regex.findall(line)
    if not saves:
        return [] 

    events = []
    for save in saves:
        player, team_abbr, total_saves = save # Jussi Rynnäs K 12+7+8=27

        e = OrderedDict()
        e["Type"] = "torjunnat"
        e["Player"] = player
        e["Team"] = full_team_name(team_abbr, home, guest)
        e["Saves"] = total_saves
        e["Time"] = 1000000000 # this should always be the last event
        events.append(e)
    return events



def eventize(stat, teams_regex):
    """ Events: End result, goal, penalties
        Given statistics text (ottelupöytäkirja), return a list of events
    """
    home_team, guest_team, events, current_score = None, None, [], (0,0)

    for line in stat.split("\n"):
        line=line.strip()

        # end result
        h, g, e = extract_endresult(line, teams_regex)
        if h is not None and g is not None:
            home_team, guest_team = h, g
            events += e

        # goals
        goals, current_score = extract_goals(line, current_score, home_team, guest_team)
        events += goals

        # penalties
        events += extract_penalties(line, home_team, guest_team)

        # goaltender saves
        events += extract_saves(line, home_team, guest_team)

        if home_team is None or guest_team is None: # dont return events if team processing failed
            return []

    return events




def print_events(idx, events, news_article, stat, output_file):

    print("##BEGINNING-OF-GAME##", file=output_file)
    print("# IDX =", idx, file=output_file)
    for line in news_article.split("\n"):
        print(line, file=output_file)
    print("="*50, file=output_file)

    events = sorted(events, key=lambda k: k["Time"])

    for i, e in enumerate(events):
        # fix few formatting issues
        if "Assist" in e:
            if e["Assist"][0]=="":
                e["Assist"]=["None"]
            e["Assist"]=", ".join(a for a in e["Assist"])
        if "Abbreviations" in e:
            e["Abbreviations"]=", ".join(a for a in e["Abbreviations"] if a!= None)
        if e["Type"] == "lopputulos" or e["Type"] == "torjunnat":
            e.pop("Time")

        # print the event
        print("E"+str(i+1), ", ".join(k+": "+str(v) for k,v in e.items()), file=output_file)

    #print(stat, file=output_file)

    print("##END-OF-GAME##", file=output_file)
    print(file=output_file)
    print(file=output_file)





def is_statistics(txt, teams_regex):
    # ottelupöytäkirja must include:
    # 1) a line with "1. erä"
    # 2) a line with lopputulos with two team names mentioned (e.g. Lukko–TPS 3–2 (0–0, 3–0, 0–2))

    if "1. erä:" not in txt and "1.erä:" not in txt:
        return False

    for line in txt.split("\n"):
        line=line.strip()
        if endresult_regex.search(line): # this is a correct line: Lukko–TPS 3–2 (0–0, 3–0, 0–2)
            hits=re.findall(teams_regex, line)
            if len(hits) >= 2:
                return True

    return False


def main(args):
    # read all data (statistics and articles, aligned with story_id)

    total_games=0
    team_counter=Counter()

    # json has (game statistics, list of news articles) pairs
    with open(args.json, "rt", encoding="utf-8") as f:
        data=json.load(f)

    # output_file
    if args.output_file == "":
        output_file = sys.stdout
    else:
        output_file = open(args.output_file, "wt", encoding="utf-8")


    # compile team regex based on known_teams list
    known_teams_txt = open(args.known_teams, "rt", encoding="utf-8").read().split("\n")
    known_teams = []
    for line in known_teams_txt:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("("):
            continue
        known_teams += line.split("|")
    teams_regex = re.compile("(?=("+'|'.join(known_teams)+r"))") # do not use ignore case here...

    # iterate over alignments
    for game_idx in data.keys():
        statistics_text = data[game_idx]["statistics"][0]["text"] # TODO: take all, not just the first one?
        news_article_text = data[game_idx]["news_articles"][0]["text"] # TODO: take all, not just the first one?
        if not is_statistics(statistics_text, teams_regex):
            statistics_text = statistics_text.replace("\n", " ", 1) # this is trying to fix line break errors
            if not is_statistics(statistics_text, teams_regex):
                continue

        events = eventize(statistics_text, teams_regex)
        if not events:
            continue
        print_events(game_idx, events, news_article_text, statistics_text, output_file)

        # collect statistics, count number of games and how many times each team appeared in the data
        total_games += 1
        team_counter.update([events[0]["Home"], events[0]["Guest"]])

    print("Initial number of alignments:", len(data.keys()), file=sys.stderr)
    print("Total number of eventized games:", total_games, file=sys.stderr)
    print("Teams:", team_counter.most_common(1000000), file=sys.stderr)


if __name__=="__main__":
    import argparse

    argparser = argparse.ArgumentParser(description='')
    
    argparser.add_argument('--json', type=str, default="/home/samuel/code/stt/data-processing/aligned_documents_100419.json", help='json filename')
    argparser.add_argument('--known_teams', type=str, default="/home/jmnybl/git_checkout/data-processing/teams_curated.txt", help='list of known team names')
    argparser.add_argument('--output_file', type=str, default="", help='output_file name, if empty prints to sys.stdout')

    args = argparser.parse_args()

    main(args)
