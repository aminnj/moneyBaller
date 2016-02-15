import Load_Games
import operator
import numpy as np
import xgboost as xgb
from sklearn.preprocessing import StandardScaler
import gzip

import pickle

def evalerror(preds, dtrain):
            labels  = dtrain.get_label()
            error_ = np.mean(    np.abs( labels - preds))
            return 'error, ' , float(error_)

np.random.seed(0)
m      = Load_Games.Load_Games(years=[2014])

teams   = m.teams
players = m.players
t_d =  m.t_d
p_d =  m.p_d
#print players[:,p_d['POSITION']]

#for line in players[0:10]:
#    print line
#    print line[p_d['POSITION']]
#print sorted( t_d.items(), key=operator.itemgetter(1))
#print sorted(p_d.items(), key=operator.itemgetter(1))

events = []
for tit,t_name in enumerate(np.unique(teams[:,t_d['TEAM_NAME_SEL']].astype(str))):
    team = []
    with gzip.open("../data/pickle/player_stats_%i.pkl" % 2014,"rb") as fh:
        data_raw = pickle.load(fh)

    team_players = players[players[:,p_d['TEAM_NAME']].astype(str) == t_name]
    team_games   = teams[teams[:,t_d["TEAM_NAME_SEL"]].astype(str) == t_name]
    other_games  = teams[teams[:,t_d["TEAM_NAME_SEL"]].astype(str) != t_name]

    other_games   = other_games[other_games[:,t_d['GAME_ID_SEL']].argsort()]
    team_players = team_players[team_players[:,p_d['GAME_ID']].argsort()]

    for gid in np.unique(team_games[:,t_d['GAME_ID_SEL']].astype(int)):
        game_p     = team_players[team_players[:,p_d["GAME_ID"]].astype(int)    ==gid]
        game_tp    = team_games [team_games[:,t_d["GAME_ID_SEL"]].astype(int)  ==gid]
        game_to    = other_games[np.searchsorted(other_games[:,t_d["GAME_ID_SEL"]].astype(int),gid)]
        other_games= other_games[np.searchsorted(other_games[:,t_d["GAME_ID_SEL"]].astype(int),gid)+1:]

        for it,range_ in enumerate(m.t_fint):
            game_p = np.c_[game_p,[game_tp[:,t_d["AVG_" + str(range_) + "_SEL"]]] * len(game_p)]
        for range_ in m.t_fint:
            game_p = np.c_[game_p,[game_to[t_d["AVG_" + str(range_) + "_OPP"]]]* len(game_p)]

        if len(team) == 0:
            team = game_p
        else:
            team = np.vstack((team,game_p))
    if len(events) == 0:
        events = team
    else:
        events = np.vstack((events,team))

dick_strings =  []
for range_ in m.t_fint:
    dick_strings.append("AVG_" + str(range_) + "_SEL")
for range_ in m.t_fint:
    dick_strings.append("AVG_" + str(range_) + "_OPP")

events_dict = m.gen_dict(np.append([s[0] for s in sorted(p_d.items(), key=operator.itemgetter(1))],dick_strings)
                              ,"None","",False)

print 'the length of events is ' +str(len(events))
print events.shape
print events[:,events_dict["AVG_" + str(m.p_fint[0])]].astype(float)
print [events[:,events_dict["AVG_" + str(m.p_fint[0])]].astype(float) == events[:,events_dict["AVG_" + str(m.p_fint[0])]].astype(float)]
print [events[:,events_dict["AVG_" + str(m.p_fint[0])]] != np.nan]

events = events[events[:,events_dict["AVG_" + str(m.p_fint[0])]].astype(float) == events[:,events_dict["AVG_" + str(m.p_fint[0])]].astype(float)]
events = events[events[:,events_dict["FANT_TARGET"]].astype(float) == events[:,events_dict["FANT_TARGET"]].astype(float)]

print 'the length of events after cleaning is ' +str(len(events))
print events.shape
print events
print sorted(events_dict.items(), key=operator.itemgetter(1))


np.random.shuffle(events)
sel_vars      = np.append(range(events_dict['FANT'],events_dict['FANT_TARGET']),range(events_dict['AVG_3_SEL'],events_dict['AVG_20_OPP']))
print sel_vars
sel_vars      = np.append(events_dict['REST'],sel_vars)
sel_vars      = np.append(events_dict['FANDUEL_SALARY'],sel_vars)
sel_vars      = np.append(events_dict['DRAFTKINGS_SALARY'],sel_vars)
sel_vars      = np.append(events_dict['FANT_PREDICTION'],sel_vars)
sel_vars      = np.append(events_dict['MATCHUP'],sel_vars)



events        = np.array(events)
vars_scaled = events[:,sel_vars].copy().astype(float)
for line in range(len(vars_scaled[0])):
    vars_scaled[:,line][vars_scaled[:,line] !=  vars_scaled[:,line]]   \
        = np.mean(vars_scaled[:,line][vars_scaled[:,line] == vars_scaled[:,line]]  )
vars_scaled   = StandardScaler().fit_transform(vars_scaled)
vars_scaled[events[:,sel_vars].astype(float) != events[:,sel_vars].astype(float)] = np.nan

train_        = vars_scaled[0:int(.9*len(events))].astype(float)
train_target  = events[0:int(.9*len(events))][:,events_dict['FANT_TARGET']]

valid_        = vars_scaled[int(.9*len(events)):].astype(float)
valid_target  = events[int(.9*len(events)):][:,events_dict['FANT_TARGET']]

dtrain_       =  xgb.DMatrix(train_, label = train_target,missing=np.nan)
dvalid_       =  xgb.DMatrix(valid_, label = valid_target,missing=np.nan)
watchlist   = [(dtrain_,'training'),(dvalid_,'validating')]


param_1     = {'max_depth':6,'eta':.05, 'silent':1,'subsample' : .5,'colsample_bytree':.75}#, #,'colsample_bytree':.75,'gamma':100,'min_child_weight':100}
num_round   = 60
bst_1         = xgb.train(param_1,dtrain_,num_round,watchlist, feval=evalerror)
preds_        = bst_1.predict(dvalid_)
mean_1 ,mean_2,counter_1= 0,0,0
for id_,line in enumerate(events[int(.9*len(events)):]):
    if float(line[events_dict["AVG_5"]]) != float(line[events_dict["AVG_5"]]):
        continue
    mean_1 += np.abs(float(line[events_dict["FANT_TARGET"]]) - float(line[events_dict["FANT_PREDICTION"]]))
    mean_2 += np.abs(float(line[events_dict["FANT_TARGET"]])- preds_[id_])
    counter_1 = counter_1 + 1
mean_1 = mean_1/counter_1
mean_2 = mean_2/counter_1
print mean_1,mean_2
