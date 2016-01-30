import json, sys, time
import numpy as np
from tqdm import tqdm
sys.path.insert(0,"../")
import utils.utils as u

np.set_printoptions(linewidth=205,formatter={'float_kind':lambda x: "%.1f" % x })

class Games:

    def __init__(self, years=[2014]):

        self.years = years

        self.info = {}
        self.team_info = {}
        self.player_info = {}

        self.combine_data()


    def combine_data(self):

        self.info["data"] = {}

        # cols to remove within the context of the game object because they are redundant with other things
        p_colremove = [ "SEASON_ID", "PLAYER_NAME", "TEAM_ABBREVIATION", "TEAM_NAME", "GAME_ID", "GAME_DATE", "MATCHUP", "WL" ]
        t_colremove = [ "SEASON_ID", "TEAM_ABBREVIATION", "TEAM_NAME", "MATCHUP" ]
        g_colremove = []

        for iyear,year in enumerate(self.years):
            p_colnames, p_data = self.load_season_json(year, "P") # player data for matches
            t_colnames, t_data = self.load_season_json(year, "T") # team data for matches
            g_colnames, g_data = self.load_season_json(year, "G") # general player data

            p_data = np.array(p_data)
            t_data = np.array(t_data)
            g_data = np.array(g_data)

            if iyear == 0:
                pcol = { p_colnames[i]:i for i in range(len(p_colnames)) }
                tcol = { t_colnames[i]:i for i in range(len(t_colnames)) }
                gcol = { g_colnames[i]:i for i in range(len(g_colnames)) }

                p_toremove = np.array([pcol[p] for p in p_colremove])
                t_toremove = np.array([tcol[t] for t in t_colremove])
                g_toremove = np.array([gcol[g] for g in g_colremove])

            self.team_info[year] = {}
            for team in t_data[np.unique(t_data[:, tcol["TEAM_ID"]], return_index=True)[1]]:
                tid = int(team[tcol["TEAM_ID"]])
                self.team_info[year][tid] = {}
                self.team_info[year][tid]["team_abbreviation"] = team[tcol["TEAM_ABBREVIATION"]]
                self.team_info[year][tid]["team_name"] = team[tcol["TEAM_NAME"]]
                self.team_info[year][tid]["opponents"] = []
                self.team_info[year][tid]["games"] = []
                self.team_info[year][tid]["players"] = []

            self.player_info[year] = {}
            for player in g_data:
                pid = int(player[gcol["PLAYER_ID"]])
                self.player_info[year][pid] = {}
                self.player_info[year][pid]["player_name"] = player[gcol["PLAYER_NAME"]]
                self.player_info[year][pid]["team"] = int(player[gcol["TEAM_ID"]])
                self.player_info[year][pid]["games"] = []

            self.info["data"][year] = {}

            gameids = np.unique(t_data[:, tcol["GAME_ID"]]).astype('int')
            # for gid in tqdm(gameids):
            for gid in tqdm(gameids[:15]):
            # for gid in ["0021400001"]:

                # FIXME THIS CAN BE MUCH FASTER
                players = p_data[ p_data[:, pcol["GAME_ID"]].astype('int')==gid ] 
                teams = t_data[ t_data[:, tcol["GAME_ID"]].astype('int')==gid ] 

                WL = teams[:,tcol["WL"]]
                if WL[0] is None: continue # NBA sucks balls and cancels some games. in this case, WL is None
                WL = (np.array(map(ord, list(WL)))-76)/11 # convert ["W", "L"] to [1,0]
                teams[:,tcol["WL"]] = WL

                teams[:,tcol["GAME_DATE"]] = map(lambda x: int(str(x).replace("-","")), list(teams[:,tcol["GAME_DATE"]])) # change "2014-10-28" to 20141028 as int

                t_ishome = np.array(["vs." in m for m in teams[:,tcol["MATCHUP"]]])
                p_ishome = np.array(["vs." in m for m in players[:,pcol["MATCHUP"]]])

                for player in players:
                    pid = int(player[pcol["PLAYER_ID"]])
                    self.player_info[year][pid]["games"].append(gid)

                tid1, tid2 = teams[:,tcol["TEAM_ID"]].astype('int')
                self.team_info[year][tid1]["opponents"].append(tid2)
                self.team_info[year][tid2]["opponents"].append(tid1)
                self.team_info[year][tid1]["games"].append(gid)
                self.team_info[year][tid2]["games"].append(gid)
                self.team_info[year][tid1]["players"].extend( list(players[players[:,pcol["TEAM_NAME"]]==self.team_info[year][tid1]["team_name"]][:,pcol["PLAYER_ID"]]) )
                self.team_info[year][tid2]["players"].extend( list(players[players[:,pcol["TEAM_NAME"]]==self.team_info[year][tid2]["team_name"]][:,pcol["PLAYER_ID"]]) )

                players = np.delete(players, p_toremove, axis=1)
                teams = np.delete(teams, t_toremove, axis=1)
                self.info["data"][year][gid] = {}
                self.info["data"][year][gid]["home_t"] = teams[t_ishome == True].astype('float')
                self.info["data"][year][gid]["opp_t"] =  teams[t_ishome == False].astype('float')
                self.info["data"][year][gid]["home_p"] = players[p_ishome == True].astype('float')
                self.info["data"][year][gid]["opp_p"] =  players[p_ishome == False].astype('float')


            # remove duplicates since we blindly extended player list many times above
            for tid in self.team_info[year].keys():
                self.team_info[year][tid]["players"] = list(np.unique(np.array(self.team_info[year][tid]["players"])))

            if iyear == 0:
                p_colnames = [cn for cn in p_colnames if cn not in p_colremove]
                t_colnames = [cn for cn in t_colnames if cn not in t_colremove]

                self.info["headers"] = {}
                self.info["headers"]["t"] = p_colnames
                self.info["headers"]["p"] = t_colnames


    def load_season_json(self, year, ptg):
        season = u.yearToSeason(year)
        filename = "../data/json/data_%s_%i.json" % (ptg, year)
        with open(filename,"r") as fh:
            data = json.loads(fh.read())
        colnames = data['resultSets'][0]['headers']
        rows = data['resultSets'][0]['rowSet']
        return colnames,rows

    # getters
    def get_game_ids(self, years=[]):
        if len(years) < 1:
            return np.unique([self.info["data"][y].keys() for y in self.info["data"].keys()])
        else:
            return np.unique([self.info["data"][y].keys() for y in years if y in self.info["data"]])

    def get_team_ids(self, years=[]):
        if len(years) < 1:
            return np.unique([self.team_info[y].keys() for y in self.team_info.keys()])
        else:
            return np.unique([self.team_info[y].keys() for y in years if y in self.team_info.keys()])

    def get_game_by_id(self, theid):
        for y in self.info["data"].keys():
            if theid in self.info["data"][y].keys():
                return self.info["data"][y][theid]
        return None

    def get_player_ids(self, years=[]):
        if len(years) < 1:
            return np.unique([self.player_info[y].keys() for y in self.player_info.keys()])
        else:
            return np.unique([self.player_info[y].keys() for y in years if y in self.player_info])

    def get_player_by_id(self, theid, years=[]):
        pyears = []
        for y in self.player_info.keys():
            if len(years) > 0 and y not in years: continue
            if theid in self.player_info[y].keys():
                pyears.append( self.player_info[y][theid] )
        return pyears

    def get_games_from_player_id(self, pid, years=[]):
        gameids = []
        for y in self.player_info.keys():
            if len(years) > 0 and y not in years: continue
            if pid in self.player_info[y].keys():
                gameids.extend( list(self.player_info[y][pid]["games"]) )
        return gameids

    def get_team_roster(self, tid, years=[]):
        rosters = []
        for y in self.team_info.keys():
            if len(years) > 0 and y not in years: continue
            if tid in self.team_info[y].keys():
                rosters.append( list(self.team_info[y][tid]["players"]) )
        return rosters

    def get_team_games(self, tid, years=[]):
        rosters = []
        for y in self.team_info.keys():
            if len(years) > 0 and y not in years: continue
            if tid in self.team_info[y].keys():
                rosters.append( list(self.team_info[y][tid]["games"]) )
        return rosters

    def get_team_opponents(self, tid, years=[]):
        rosters = []
        for y in self.team_info.keys():
            if len(years) > 0 and y not in years: continue
            if tid in self.team_info[y].keys():
                rosters.append( list(self.team_info[y][tid]["opponents"]) )
        return rosters


if __name__=='__main__':
    # g = Games(years=[2010,2011,2012,2013,2014])
    g = Games(years=[2014])

    # print g.get_game_ids(years=[2014])
    # print g.get_game_by_id(21400002)
    # print g.get_player_ids(years=[2014])
    # print g.get_games_from_player_id(201167)
    # print g.get_player_by_id(201167)
    # print g.get_team_ids(years=[2014])
    # print g.get_team_roster(1610612743)
    # print g.get_team_games(1610612743)
    # print g.get_team_opponents(1610612743)

