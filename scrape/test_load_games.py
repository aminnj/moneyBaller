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

def gen_key(p_,m):
    d_ = {}
    vars = np.append( ["AVG_" + str(s) + "_" +"POSITION_OPP" for s in m.t_fint],
                      np.append(["AVG_" + str(s) for s in m.p_fint],p_) )
    for id_,line in enumerate(vars):
        d_[line] = id_
    return d_

np.random.seed(0)
m      = Load_Games.Load_Games(years=[2014])

teams   = m.teams
players = m.players


t_d =  m.t_d
p_d =  m.p_d

players[players[:,p_d['POSITION']].astype(str)  == "Center-Forward"][:,p_d['POSITION']] = "Center"
players[players[:,p_d['POSITION']].astype(str)  == "Guard-Forward"] = "Guard"
#players[players[:,p_d['POSITION']].astype(str)  == "Forward-Guard"] = "Forward"

print 'The sorted team items are ' + str(sorted( t_d.items(), key=operator.itemgetter(1)))
print 'The sorted player items are ' + str(sorted(p_d.items(), key=operator.itemgetter(1)))

events = []
p_ = [p_d['REST'],p_d['FANDUEL_SALARY'],p_d['DRAFTKINGS_SALARY'],p_d['MATCHUP'],p_d["FANT_PREDICTION"],p_d["POSITION"],p_d['FANT_TARGET']]
p_names = [['REST'],['FANDUEL_SALARY'],['DRAFTKINGS_SALARY'],['MATCHUP'],['FANT_PREDICTION'],['POSITION'],['FANT_TARGET']]
d_ = gen_key(p_names,m)
print d_.keys()

for t_name in np.unique(teams[:,t_d['TEAM_NAME_SEL']].astype(str)):
    team_players = players[players[:,p_d['TEAM_NAME']].astype(str) == t_name]
    team_games   = teams[teams[:,t_d["TEAM_NAME_SEL"]].astype(str) == t_name]

    for game in team_games:
        gid = game[t_d['GAME_ID_SEL']]
        for player in team_players[team_players[:,p_d['GAME_ID']] == gid]:
            event = []
            g_vars = map(lambda x: t_d[x] ,["AVG_" + str(s) + "_" + player[p_d['POSITION']] + "_OPP" for s in m.t_fint])
            p_vars = np.append(map(lambda x: p_d[x],["AVG_" + str(s) for s in m.p_fint]),p_)

            for line in g_vars:
                event.append(game[line])

            for line in p_vars:
                event.append(player[line])
            events.append(event)

events        = np.array(events)
events        = events[events[:,d_['AVG_9']].astype(float) == events[:,d_['AVG_9']].astype(float)]
events        = events[events[:,d_['FANT_TARGET']].astype(float) == events[:,d_['FANT_TARGET']].astype(float)]

pos_ = {}
for id_,line in enumerate(m.positions):
   pos_[line] = id_
events[:,d_['POSITION']] = map(lambda x: pos_[x] ,events[:,d_['POSITION']])

X       = events[:,range(0,d_['FANT_TARGET'])]
y       = events[:,d_['FANT_TARGET']]


vars_scaled = X.copy().astype(float)
for line in range(len(vars_scaled[0])):
    vars_scaled[:,line][vars_scaled[:,line] !=  vars_scaled[:,line]]   \
        = np.mean(vars_scaled[:,line][vars_scaled[:,line] == vars_scaled[:,line]]  )
vars_scaled   = StandardScaler().fit_transform(vars_scaled)

vars_scaled[X.astype(float) != X.astype(float)] = np.nan

train_        = X[0:int(.9*len(events))].astype(float)
train_target  = y[0:int(.9*len(events))].astype(float)

valid_        = X[int(.9*len(events)):].astype(float)
valid_target  = y[int(.9*len(events)):].astype(float)

dtrain_       =  xgb.DMatrix(train_, label = train_target,missing=np.nan)
dvalid_       =  xgb.DMatrix(valid_, label = valid_target,missing=np.nan)
watchlist   = [(dtrain_,'training'),(dvalid_,'validating')]


param_1     = {'max_depth':2,'eta':.05, 'silent':1}#,#'subsample' : .5,'colsample_bytree':.75}#, #,'colsample_bytree':.75,'gamma':100,'min_child_weight':100}
num_round   = 100
bst_1         = xgb.train(param_1,dtrain_,num_round,watchlist, feval=evalerror)
preds_        = bst_1.predict(dvalid_)
mean_1 ,mean_2,counter_1= 0,0,0
for id_,line in enumerate(events[int(.9*len(events)):]):
    if float(line[d_["AVG_5"]]) != float(line[d_["AVG_5"]]):
        continue
    mean_1 += np.abs(float(line[d_["FANT_TARGET"]]) - float(line[d_["FANT_PREDICTION"]]))
    mean_2 += np.abs(float(line[d_["FANT_TARGET"]])- preds_[id_])
    counter_1 = counter_1 + 1
mean_1 = mean_1/counter_1
mean_2 = mean_2/counter_1
print mean_1,mean_2
