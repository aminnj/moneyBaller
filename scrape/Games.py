import json, sys, time
import numpy as np
import pickle, gzip
from tqdm import tqdm
sys.path.insert(0,"../")
import utils.utils as u

np.set_printoptions(linewidth=205,formatter={'float_kind':lambda x: "%.1f" % x })

class Games:

    def __init__(self, years=[2014], debug=False):

        self.years = years
        self.debug = debug

        self.info = {}
        self.team_info = {}
        self.player_info = {}

        self.combine_data()
        # self.pickle_data()
        # self.unpickle_data()

    def pickle_data(self, outfile="../data/pickle.pkl"):
        # with gzip.open(outfile,"wb") as fh:
        with open(outfile,"wb") as fh:
            pickle.dump([self.years, self.info, self.team_info, self.player_info], fh)
        print "Pickled years %s into %s" % (",".join(map(str,self.years)), outfile)

    def unpickle_data(self, infile="../data/pickle.pkl"):
        # with gzip.open(infile,"rb") as fh:
        with open(infile,"rb") as fh:
            self.years, self.info, self.team_info, self.player_info = pickle.load(fh)
        print "Unpickled years %s from %s" % (",".join(map(str,self.years)), infile)


    def combine_data(self):

        self.info["data"] = {}

        # cols to remove within the context of the game object because they are redundant with other things
        p_colremove = [ "SEASON_ID", "PLAYER_NAME", "TEAM_ABBREVIATION", "TEAM_NAME", "GAME_DATE", "MATCHUP", "WL" ]
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

                p_colnamesnew = [cn for cn in p_colnames if cn not in p_colremove]
                t_colnamesnew = [cn for cn in t_colnames if cn not in t_colremove]
                g_colnamesnew = [cn for cn in g_colnames if cn not in g_colremove]

                pcolnew = { p_colnamesnew[i]:i for i in range(len(p_colnamesnew)) }
                tcolnew = { t_colnamesnew[i]:i for i in range(len(t_colnamesnew)) }
                gcolnew = { g_colnamesnew[i]:i for i in range(len(g_colnamesnew)) }

                self.info["headers"] = {}
                self.info["headers"]["t"] = t_colnamesnew
                self.info["headers"]["p"] = p_colnamesnew
                self.info["headers"]["g"] = g_colnamesnew


            self.team_info[year] = {}
            for team in t_data[np.unique(t_data[:, tcol["TEAM_ID"]], return_index=True)[1]]:
                tid = int(team[tcol["TEAM_ID"]])
                self.team_info[year][tid] = {}
                self.team_info[year][tid]["team_abbreviation"] = team[tcol["TEAM_ABBREVIATION"]]
                self.team_info[year][tid]["name"] = team[tcol["TEAM_NAME"]]
                self.team_info[year][tid]["opponents"] = []
                self.team_info[year][tid]["games"] = []
                self.team_info[year][tid]["players"] = []

            self.player_info[year] = {}
            for player in g_data:
                pid = int(player[gcol["PLAYER_ID"]])
                self.player_info[year][pid] = {}
                self.player_info[year][pid]["name"] = player[gcol["PLAYER_NAME"]]
                self.player_info[year][pid]["team"] = int(player[gcol["TEAM_ID"]])
                self.player_info[year][pid]["age"] = int(float(player[gcol["AGE"]]))
                self.player_info[year][pid]["games"] = []

            self.info["data"][year] = {}

            gameids = np.unique(t_data[:, tcol["GAME_ID"]]).astype('int')
            p_gidLUT = { int(gid): [] for gid in gameids }
            t_gidLUT = { int(gid): [] for gid in gameids }
            for p in p_data:
                gid = int(p[pcol["GAME_ID"]])
                p_gidLUT[gid].append(p)
            for t in t_data:
                gid = int(t[tcol["GAME_ID"]])
                t_gidLUT[gid].append(t)

            # for gid in ["0021400001"]:
            # for igid,gid in enumerate(gameids):
            for igid,gid in tqdm(enumerate(gameids)):

                if self.debug and igid > 175: break

                players = np.array(p_gidLUT[gid])
                teams = np.array(t_gidLUT[gid])

                WL = teams[:,tcol["WL"]]
                if WL[0] is None: continue # NBA sucks balls and cancels some games. in this case, WL is None
                WL = (np.array(map(ord, list(WL)))-76)/11 # convert ["W", "L"] to [1,0]
                teams[:,tcol["WL"]] = WL

                teams[:,tcol["GAME_DATE"]] = map(lambda x: int(str(x).replace("-","")), list(teams[:,tcol["GAME_DATE"]])) # change "2014-10-28" to 20141028 as int

                t_ishome = np.array(["vs." in m for m in teams[:,tcol["MATCHUP"]]])
                p_ishome = np.array(["vs." in m for m in players[:,pcol["MATCHUP"]]])

                tid1, tid2 = teams[:,tcol["TEAM_ID"]].astype('int')
                self.team_info[year][tid1]["opponents"].append(tid2)
                self.team_info[year][tid2]["opponents"].append(tid1)
                self.team_info[year][tid1]["games"].append(gid)
                self.team_info[year][tid2]["games"].append(gid)
                self.team_info[year][tid1]["players"].extend( list(players[players[:,pcol["TEAM_NAME"]]==self.team_info[year][tid1]["name"]][:,pcol["PLAYER_ID"]]) )
                self.team_info[year][tid2]["players"].extend( list(players[players[:,pcol["TEAM_NAME"]]==self.team_info[year][tid2]["name"]][:,pcol["PLAYER_ID"]]) )

                # after we delete the columns, we must use pcolnew to get columns
                players = np.delete(players, p_toremove, axis=1)
                teams = np.delete(teams, t_toremove, axis=1)

                self.info["data"][year][gid] = {}
                self.info["data"][year][gid]["home_t"] = teams[t_ishome == True].astype('float')[0]
                self.info["data"][year][gid]["opp_t"] =  teams[t_ishome == False].astype('float')[0]
                self.info["data"][year][gid]["home_p"] = players[p_ishome == True].astype('float')
                self.info["data"][year][gid]["opp_p"] =  players[p_ishome == False].astype('float')

                for player in players:
                    # print player
                    # print pcolnew["PLAYER_ID"]
                    pid = int(player[pcolnew["PLAYER_ID"]])
                    # print pid
                    pindex = np.where(players[:,pcolnew["PLAYER_ID"]]==pid)[0][0] # should ALWAYS find the player in the game
                    self.player_info[year][pid]["games"].append(players[pindex])
                    # print players[pindex]

            # remove duplicates since we blindly extended player list many times above
            for tid in self.team_info[year].keys():
                self.team_info[year][tid]["players"] = list(np.unique(np.array(self.team_info[year][tid]["players"])))

            for pid in self.player_info[year].keys():
                if len(self.player_info[year][pid]["games"]) < 1: continue
                self.player_info[year][pid]["games"] = np.array([tuple(p) for p in self.player_info[year][pid]["games"]], dtype=[(str(col), np.float) for col in pcolnew])

                # print self.player_info[year][pid]["games"]





    def load_season_json(self, year, ptg):
        season = u.yearToSeason(year)
        filename = "../data/json/data_%s_%i.json" % (ptg, year)
        with open(filename,"r") as fh:
            data = json.loads(fh.read())
        colnames = data['resultSets'][0]['headers']
        rows = data['resultSets'][0]['rowSet']
        return colnames,rows

    def collapse(self, inp):
        if len(self.years) == 1:
            if type(inp) is list and len(inp) > 0:
                return inp[0]
        return inp

    def order_game_ids_by_date(self, gameids, desc=False):
        # take advantage of the fact that ascending gameids means ascending dates
        return sorted(gameids, reverse=desc)
        

    # GETTERS
    def get_game_ids(self, years=[], desc=False,flatten=True):
        toreturn = None
        if len(years) < 1:
            toreturn = np.unique([self.info["data"][y].keys() for y in self.info["data"].keys()])
        else:
            toreturn = np.unique([self.info["data"][y].keys() for y in years if y in self.info["data"]])
        toreturn = self.order_game_ids_by_date(toreturn, desc)
        if flatten: return sum(toreturn, [])
        else: return toreturn

    def get_team_ids(self, years=[]):
        if len(years) < 1:
            return np.unique([self.team_info[y].keys() for y in self.team_info.keys()])
        else:
            return np.unique([self.team_info[y].keys() for y in years if y in self.team_info.keys()])

    def get_game_by_id(self, theid, recarray=True):
        game = None
        for y in self.info["data"].keys():
            if theid in self.info["data"][y].keys():
                game = self.info["data"][y][theid]
        if game == None: return game

        if recarray:
            tcols = self.info["headers"]["t"]
            pcols = self.info["headers"]["p"]
            # print theid
            thegame = {}
            thegame["home_t"] = np.array([tuple(game["home_t"])], dtype=[(str(col), np.float) for col in tcols])
            thegame["opp_t"] = np.array([tuple(game["opp_t"])], dtype=[(str(col), np.float) for col in tcols])
            thegame["home_p"] = np.array([tuple(p) for p in game["home_p"]], dtype=[(str(col), np.float) for col in pcols])
            thegame["opp_p"] = np.array([tuple(p) for p in game["opp_p"]], dtype=[(str(col), np.float) for col in pcols])

        return game

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
        return self.collapse(pyears)

    def get_games_from_player_id(self, pid, years=[], desc=False):
        gameids = []
        for y in self.player_info.keys():
            if len(years) > 0 and y not in years: continue
            if pid in self.player_info[y].keys():
                gameids.append( self.order_game_ids_by_date(list(self.player_info[y][pid]["games"]),desc) )
        return self.collapse(gameids)

    def get_team_roster(self, tid, years=[]):
        rosters = []
        for y in self.team_info.keys():
            if len(years) > 0 and y not in years: continue
            if tid in self.team_info[y].keys():
                rosters.append( list(self.team_info[y][tid]["players"]) )
        return self.collapse(rosters)

    def get_team_games(self, tid, years=[], desc=False):
        games = []
        for y in self.team_info.keys():
            if len(years) > 0 and y not in years: continue
            if tid in self.team_info[y].keys():
                games.append( self.order_game_ids_by_date(list(self.team_info[y][tid]["games"]),desc) )
        return self.collapse(games)

    def get_team_opponents(self, tid, years=[]):
        rosters = []
        for y in self.team_info.keys():
            if len(years) > 0 and y not in years: continue
            if tid in self.team_info[y].keys():
                rosters.append( list(self.team_info[y][tid]["opponents"]) )
        return self.collapse(rosters)
    
    def get_player_column_names(self):
        return self.info["headers"]["p"]

    def get_game_column_names(self):
        return self.info["headers"]["t"]

    def get_date_from_gameid(self, gid):
        return int(self.get_game_by_id(gid,recarray=False)["home_t"][self.info["headers"]["t"].index("GAME_DATE")])

    def get_years(self):
        return self.years

if __name__=='__main__':
    pass
    # g = Games(years=[2010,2011,2012,2013,2014])
    # g = Games(years=[2010,2011,2012,2013,2014,2015])
    # g = Games(years=[2014], debug=True)

    # # Some basic function calls
    # print g.get_game_ids(years=[2014])
    # print g.get_game_by_id(21400002)
    # print g.get_player_ids(years=[2014])
    # print g.get_games_from_player_id(201951, desc=True) # order game ids with descending date
    # print g.get_player_by_id(201167)
    # print g.get_team_ids(years=[2014])
    # print g.get_team_roster(1610612743)
    # print g.get_team_games(1610612743)
    # print g.get_team_opponents(1610612743)
    # print g.get_player_column_names()
    # print g.get_game_column_names()
    # print g.get_date_from_gameid(21400002)
    
    # # Get the team roster given a player
    # teamid = g.get_player_by_id(201167)["team"]
    # for pid in g.get_team_roster(teamid):
    #     print g.get_player_by_id(pid)["name"],
    #     print g.get_player_by_id(pid)["age"]

    # # Slightly more complicated: how often do home teams win?
    # wl = []
    # for gid in g.get_game_ids():
    #     game = g.get_game_by_id(gid)
    #     wl.append( game["home_t"]["WL"] )
    # print "Home teams win %.1f%% of the time (from %i games)" % (100.0*np.mean(wl), len(wl))

    # with open("../data/hometowns.pkl","r") as fh:
    #     dHometowns = pickle.load(fh)

    # print len(dHometowns.keys())

    # pids = sum(g.get_player_ids(),[])
    # print len(pids)

    # cnt = 0
    # for pid in pids:
    #     name = g.get_player_by_id(pid)[0]["name"]
    #     if name in dHometowns:
    #         cnt += 1
    # print cnt
