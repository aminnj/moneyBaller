import requests, json, urllib2, urllib
import datetime, ast, sys
import pprint, itertools

BASE_URL = 'http://api.sportsdatabase.com/nba/query.json?sdql='
API_KEY = 'guest'

def getGames(params, season):
    today = datetime.datetime.now().strftime("%Y%m%d")
    requrl = "%s%s@season=%i&date<=%s&output=json&api_key=%s" % (BASE_URL, params, season,today,API_KEY)
    req = requests.get(requrl)
    data = req.content[14:-3]
    js = ast.literal_eval(data)
    headers = js["headers"]
    maindata = js["groups"][0]["columns"]

    games = []
    for irow in range(len(maindata[0])):
        d = { headers[icol] : maindata[icol][irow] for icol in range(len(headers)) }
        d["season"] = season
        games.append(d)
    
    return games

if __name__ == '__main__':
    mainparams = []
    single = ["playoffs", "minutes", "lead changes", "month", "officials", "total", "time of game", "overtime", "season", "times tied", "date", "ou margin", "day"]
    both = ["assists", "ats margin", "ats streak", "biggest lead", "blocks", "conference", "date", "day", "defensive rebounds", "division", "dpa", "dps", "fast break points", "field goals attempted", "field goals made", "fouls", "free throws attempted", "free throws made", "game number", "lead changes", "line", "losses", "margin", "margin after the first", "margin after the third", "margin at the half", "matchup losses", "matchup wins", "minutes", "month", "offensive rebounds", "officials", "season", "rebounds", "site", "ou margin", "ou streak", "overtime", "playoffs", "points", "points in the paint", "quarter scores", "turnovers", "wins", "three pointers attempted", "three pointers made", "time of game", "times tied", "total", "site streak", "steals", "streak", "team", "team rebounds"]

    mainparams.extend( single )
    mainparams.extend( map(lambda x: "".join(list(x)), list(itertools.product(["o:","t:"],both))) )
    mainparams = ",".join(mainparams)

    print "[scrape] Fetching parameters: %s" % mainparams

    seasons = range(2015, 2001, -1)

    with open("../data/out.txt", "w") as fhout:
        for season in seasons:
            try:
                games = getGames(mainparams, season)
                print "[scrape] got games for season %i" % season
            except:
                print "[scrape] ERROR getting games for season %i" % season
                continue

            for game in games:
                fhout.write(str(game) + "\n")
