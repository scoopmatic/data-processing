import sys
import json
import re
from collections import Counter



def plot(plot_statistics, plot_alignments):
    # plot statistics/plot_alignments: list of (year, number) -tuples

    import matplotlib.pyplot as plt

    plt.subplot(1, 2, 1)
    x=[year for year, number in plot_statistics]
    y=[number for year, number in plot_statistics]
    plt.plot(x, y, 'ko-')
    plt.title('Existing statistics')
    plt.xlabel('Year')
    plt.ylabel('Number of files')


    plt.subplot(1, 2, 2)
    x=[year for year, number in plot_alignments]
    y=[number for year, number in plot_alignments]
    plt.plot(x, y, 'ro-')
    plt.title('Aligned statistics')
    plt.xlabel('Year')
    plt.ylabel('Number of files')

    #plt.show()




def read_json(fname):

    documents={}

    with open(fname, "rt", encoding="utf-8") as f:
        for i, document in enumerate(f):
            document=document.strip()
            if not document:
                continue
            try:
                data=json.loads(document)
            except json.decoder.JSONDecodeError:
                print("Invalid line:", document, file=sys.stderr)
            if data["topic-id"] is not None: # index based on topic-id
                key=data["topic-id"]
            else:
                key=data["timestamp"][:8] # index based on date
            if key not in documents:
                documents[key]=[]
            documents[key].append(data)
    return documents


endresult=re.compile("\([0-9]+(\u2013|-)[0-9]+,\s?[0-9]+(\u2013|-)[0-9]+,\s?[0-9]+(\u2013|-)[0-9]+", re.UNICODE) # (1–1, 1–1, 1–0
teams_regex=re.compile("(?=([A-ZÜÅÄÖa-züåäö\-0-9]+\u2013[A-ZÜÅÄÖa-züåäö\-0-9]+))", re.UNICODE) # Lukko–TPS
score_regex=re.compile("[0-9]+(\u2013|-)[0-9]+.*\([0-9]+(\u2013|-)[0-9]+,\s?[0-9]+(\u2013|-)[0-9]+,\s?[0-9]+(\u2013|-)[0-9]+", re.UNICODE) # (1–1, 1–1, 1–0

known_teams_txt = open("teams_curated.txt").read().split('\n')
known_teams_txt = [line for line in known_teams_txt if not line.startswith('#')]
known_teams = [(team.split('|')[0], re.compile("(\W|^)("+team+")(\W|$)", re.IGNORECASE)) for team in known_teams_txt if team] # Compiled
known_teams_src = {team.split('|')[0]: "(\W|^)("+team+")(\W|$)" for team in known_teams_txt if team} # Uncompiled

def extract_teams(txt):

    teams=[]
    for line in txt.split("\n"):
        line=line.strip()
        for team, pat in known_teams:
            match = pat.search(line)
            if match:
                teams.append((match.start(), team))
            if len(teams) >= 2:
                break
        if len(teams) >= 2:
            break
        if endresult.search(line): # this is a correct line: Lukko–TPS 3–2 (0–0, 3–0, 0–2)
            break

            ### Extracting team names by contextual pattern (high precision)
            """try:
                hits=re.findall(teams_regex, line[:score_regex.search(line).start()])
            except AttributeError:
                print("No match:",line)

            if not hits:
                continue
            home,guest=hits[0].split("\u2013")
            teams.append(home)
            teams.append(guest)"""

            ### Extracting team names by contextual pattern (high recall)
            """teams = line[:endresult.search(line).start()]
            teams = teams.replace('\u2013v.','-v.')
            teams = teams.replace('\u2013vuot','-vuot')
            teams = teams.split('\u2013')"""

    return [x for _,x in sorted(teams)]


def separate_statistics(stats_txt):
    # returns a list of game statistics (originally one statistics file can have multiple games, now split those)
    # Identifies new game by possible team name pairs, not scores (which might be missing or placed on separate line)
    statistics=[]
    lines=[]

    for line in stats_txt.split("\n"):
        line=line.strip()
        if re.search(u'[A-Za-zÅÄÖåäö]\u2013[A-Za-zÅÄÖåäö]', line[:25]): # possible team occurrence
            for team, pat in known_teams:
                if pat.search(line.split(u'\u2013')[0]):
                    # New stat starts
                    if lines: # Not the first stat in doc
                        statistics.append('\n'.join(lines))
                        lines = []
                    lines.append(line)
                    break
            else:
                if lines:
                    lines.append(line)
        elif lines:
            lines.append(line)

    if lines:
        statistics.append('\n'.join(lines))
    return statistics


def align(statistics, news):
    aligned_documents={}
    counter=0
    uncounter=0
    years=Counter()

    known_teams = set()
    import copy
    for key, stat_documents in statistics.items():
        teams=[]
        for d in stat_documents: # iterate over all statistics from this one day or topic-id
            game_stats=separate_statistics(d["text"])

            for gi, game in enumerate(game_stats): # iterate over games
                curr_teams=extract_teams(game)

                if len(curr_teams) != 2:
                    print("Team extraction error:", curr_teams, file=sys.stderr)
                    print("Game",gi,game+'\n', file=sys.stderr)
                    print("--",file=sys.stderr)
                    print(d["text"]+'\n', file=sys.stderr)
                    print(file=sys.stderr)
                    continue

                """
                ### Code for cleaning team name candidates from high-recall version of extract_teams(), for building list of known teams
                found_new = False
                for team in curr_teams:
                    if team not in known_teams:
                        team = re.sub(".*maaottelu ", "", team)
                        team = re.sub(".*: ", "", team)

                        team = re.sub("\(?[0-9]+\-v\.\)?", "", team)
                        team = re.sub("(n alle )?[0-9]+\-vuotiaat", "", team)
                        team = re.sub("[0-9]+\-vuotiaiden", "", team)
                        team = re.sub("[0-9]+v.? ?$", "", team)
                        team = re.sub(" U[0-9]+ ?$", "", team)

                        team = re.sub(" j\.a\.?", "", team, re.IGNORECASE)
                        team = re.sub(" rl\.?", "", team, re.IGNORECASE)
                        team = re.sub(" vl\.?", "", team, re.IGNORECASE)
                        team = re.sub(" je\.?", "", team, re.IGNORECASE)

                        team = re.sub(" [0-9]\.? *", "", team)
                        team = team.strip()
                        if len(team) > 1:
                            print("New team:", team)
                            known_teams.add(team)
                            found_new = True
                if found_new:
                    print(game.split('\n')[0][:50])
                    print()"""

                assert len(curr_teams)>=2

                articles=[]
                tries = 0

                tmpkey = copy.copy(key)
                while not articles:
                    if tmpkey not in news:
                        break
                    for article in news[tmpkey]: #try to find news articles labeled with this same key, skip statistics
                        if article['article-type'] == 'statistics':#is_statistics(article["text"]):
                            continue
                        # try to find team mentions
                        if match_articles(article["text"], curr_teams): # correct news article
                            articles.append(article)
                            #print(curr_teams)
                            #print(article['text'])
                            #print()

                    if not articles:
                        try:
                            tmpkey = "%s" % (int(tmpkey)+1) # Lazy iteration of days, doesn't yield many more hits anyway
                        except ValueError: # Is probably not a date
                            break
                        tries += 1
                        if tries >= 2: # Expected publishing lag
                            break

                #print()
                if not articles:
                    #print()#print("No articles found:", key, curr_teams)
                    uncounter += 1
                    continue
                #if len(articles) > 1:
                #    print("Multiple matches:", len(articles), key, curr_teams)

                i = 0
                #while True:
                #    #new_key = "%s-%d-%d" % (tmpkey,gi,i)
                #    new_key = "%s-%s-%s-%d" % (tmpkey, curr_teams[0], curr_teams[1], i)
                new_key = "%s-%s-%s" % (tmpkey, curr_teams[0], curr_teams[1])
                if new_key not in aligned_documents:
                    aligned_documents[new_key]={"teams": curr_teams, "statistics": [], "news_articles": articles}
                #i += 1

                #aligned_documents[new_key]={"game_idx": gi, "teams": curr_teams, "statistics": game, "game_hash":"%.6d" % (abs(hash(game)) % 10**6),  "stat_file": d["file_name"], "news_articles": articles}
                aligned_documents[new_key]["statistics"].append({"game_idx": gi, "text": game, "game_hash":"%.6d" % (abs(hash(game)) % 10**6),  "file_name": d["file_name"]})

                counter+=1
                years.update([int(articles[0]["timestamp"][:4])])

    #open("known_teams3", "w").write('\n'.join(list(known_teams))) # Save harvested team name candidates

    print("Number of aligned rounds:", len(aligned_documents.keys()), file=sys.stderr)
    print("Years (alignments):", sorted(years.items()))
    print(counter, uncounter)

    return aligned_documents, sorted(years.items())



def match_articles(news_text, team_query, threshold=7):

    for team in team_query:
        team_regex=re.compile("(?=("+known_teams_src[team]+r"))", re.UNICODE)
        if not team_regex.search(news_text[:250]):
            return False
    if score_regex.search(news_text):
        return False
    if len(teams_regex.findall(news_text)[:250]) > threshold:
        #print("Multiple matches:", news_text[:150])
        return False
    if re.search("(rahapelit|tuloksia|taulukko|tilastoja|tilastot|järjestys|pörssi:?|pörssejä|siirrot|ohjelma|Taitoluistelua) ?[\n/]", news_text):
        return False
    return True



def is_statistics(txt):
    # ottelupöytäkirja must include:
    # 1) a line with "1. erä"
    # 2) a line with lopputulos with two team names mentioned (e.g. Lukko–TPS 3–2 (0–0, 3–0, 0–2))

    if "1. erä:" not in txt and "1.erä:" not in txt:
        return False
    if len(extract_teams(txt)) < 2:
        return False
    return True



def find_statistics(news):
    # exctract all ottelupöytäkirja from the news article dump

    statistics={}
    years=Counter()

    for key, documents in news.items():
        for i, d in enumerate(documents):
            if is_statistics(d["text"]):
                d["article-type"]="statistics"
                if key not in statistics:
                    statistics[key]=[]
                statistics[key].append(d)
                years.update([int(d["timestamp"][:4])])
            else:
                d["article-type"]="news"
    print("Number of rounds with statistics:", len(statistics.keys()))
    print("Years (statistics):", sorted(years.items()))
    return statistics, sorted(years.items())

def main(args):

    # read combined news article + statistics data from a given json
    # returns a dictionary where key: topic-id or timestamp, value: list of articles/statistics (dictonaries) assigned to a topic-id, or timestamp
    news_documents = read_json(args.json)

    # find all statistics (ottelupöytäkirja) from news documents
    # returns a dictionary where key: topic-id or timestamp, value: list of statistics dictonaries
    statistics, plot_statistics = find_statistics(news_documents)

    # align statistics and articles
    # returns a dictionary where key: topic-id or timestamp, value: list of aligned statistics and news articles (with article-type marked)
    aligned_documents, plot_alignments = align(statistics, news_documents)

    # extra visualization to make sure we do not have weird missing data
    plot(plot_statistics, plot_alignments)

    # save
    with open("aligned_documents.json", "wt", encoding="utf-8") as f:
        json.dump(aligned_documents, f, indent=2, sort_keys=True)





if __name__=="__main__":
    import argparse

    argparser = argparse.ArgumentParser(description='')

    argparser.add_argument('--json', type=str, default="/home/jmnybl/stt-data-clean/all_news_stats.jsonl", help='json filename')

    args = argparser.parse_args()

    main(args)
