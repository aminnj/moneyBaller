import requests, json

def getData(season, playerOrTeam="P"):
    requrl="http://stats.nba.com/stats/leaguegamelog?Direction=DESC&LeagueID=00&PlayerOrTeam=%s&Season=%s&SeasonType=Regular+Season&Sorter=PTS" % (playerOrTeam, season)
    headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36"}
    req = requests.get(requrl, headers=headers, timeout=30)
    return req.json()

if __name__=='__main__':
    for year in range(2000,2016):
        season = "%s-%s" % (str(year), str(year+1)[-2:])
        for pt in ["P", "T"]:
            try:
                data = getData(season, playerOrTeam=pt)
                outname = "../data/json/data_%s_%i.json" % (pt, year)
                with open(outname,"w") as fh:
                    json.dump(data, fh)
                print "[scraper] Got %s data for %s" % ("player" if pt == "P" else "team", season)
            except:
                print "[scraper] ERROR getting %s data for %s" % ("player" if pt == "P" else "team", season)



