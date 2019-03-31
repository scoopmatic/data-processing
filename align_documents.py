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

    plt.show()




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
teams_regex=re.compile("(?=([A-ZÅÄÖa-zåäö-]+\u2013[A-ZÅÄÖa-zåäö-]+))", re.UNICODE) # Lukko–TPS

def extract_teams(txt):
    #TODO: modify teams_regex to take into account known teams with whitespace (only from statistics, no need to include 'Hämeenlinnan Pallokerho')
    # e.g. Hermes HT, AC HaKi, Erä III, D Team

    # maybe something like this?
    #team_names = ['KooKoo', 'KalPa', 'Tappara', 'Ilves', 'HPK', 'Kärpät', 'Jokerit'] #jne. from known_teams
    #teams_regex=re.compile("(?=("+'|'.join(team_names)+r"))", re.IGNORECASE)


    teams=[]

    for line in txt.split("\n"):
        line=line.strip()
        if endresult.search(line): # this is a correct line: Lukko–TPS 3–2 (0–0, 3–0, 0–2)
            print(line)
            hits=re.findall(teams_regex, line)
            if not hits:
                continue
            home,guest=hits[0].split("\u2013")
            teams.append(home)
            teams.append(guest)
    return teams


def separate_statistics(stats_txt):
    # returns a list of game statistics (originally one statistics file can have multiple games, now split those)
    statistics=[]
    lines=[]
    for line in stats_txt.split("\n"):
        line=line.strip()
        if endresult.search(line): # new game starts
            if lines:
                statistics.append("\n".join(lines))
            lines=[]
            lines.append(line)
            continue
        if lines: # add 'misc' line only if not empty (this is to skip lines before the first endresult line)
            lines.append(line)
    if lines:
        statistics.append("\n".join(lines))
    return statistics

def align(statistics, news):

    aligned_documents={}
    counter=0
    years=Counter()

    for key, stat_documents in statistics.items():
        teams=[]
        for d in stat_documents: # iterate over all statistics from this one day or topic-id
            game_stats=separate_statistics(d["text"])
            for game in game_stats: # iterate over games
                curr_teams=extract_teams(game)
                teams+=curr_teams # remove this line after finihing the function
                # TODO: out-of-time, continue here!!!!
                # article 'for article in news[key]' loop should be inside this one, so that for each game, we get a list of aligned news articles
                # --> annotator will then do sentence-game event alignment for a given game statistics-news article pair
        assert len(teams)>=2

        articles=[]
        for article in news[key]: #try to find news articles labeled with this same key, skip statistics TODO: how to recognize news article from statistics?
            if is_statistics(article["text"]):
                continue
            # try to find team mentions
            if match_articles(article["text"], teams): # correct news article
                article["article-type"]="news"
                articles.append(article)

        if not articles:
            continue
        aligned_documents[key]={"statistics": stat_documents, "news_articles": articles, "teams":teams}

        counter+=1
        years.update([int(articles[0]["timestamp"][:4])])
    
    print("Number of aligned rounds:", len(aligned_documents.keys()), file=sys.stderr)
    print("Years (alignments):", sorted(years.items()))

    return aligned_documents, sorted(years.items())





def match_articles(news_text, known_teams, threshold=3):

    team_regex=re.compile("(?=("+'|'.join(known_teams)+r"))", re.UNICODE)
    if not team_regex.search(news_text) or len(team_regex.findall(news_text))<threshold: # check whether news article has the correct team mentions
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
        for d in documents:
            if is_statistics(d["text"]):
                d["article-type"]="statistics"
                if key not in statistics:
                    statistics[key]=[]
                statistics[key].append(d)
                years.update([int(d["timestamp"][:4])])
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
        json.dump(aligned_documents, f, indent=2)





if __name__=="__main__":
    import argparse

    argparser = argparse.ArgumentParser(description='')
    
    argparser.add_argument('--json', type=str, default="all_news_stats.jsonl", help='json filename')

    args = argparser.parse_args()

    main(args)














