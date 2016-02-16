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

def gen_key(g_,p_,m):
    d_ = {}
    vars = np.append( g_,
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

g_vars = np.append(np.append(['AVG_' + s + "_SEL" for s in np.array(m.t_inclusive).astype(str)],
                             ['AVG_' + s + "_OPP" for s in np.array(m.t_inclusive).astype(str)]),
                             ["AVG_" + str(s) + "_" +"POSITION_OPP" for s in m.t_fint])

p_vars = [['REST'],['FANDUEL_SALARY'],['DRAFTKINGS_SALARY'],['MATCHUP'],['FANT_PREDICTION'],['POSITION'],['FANT_TARGET']]
d_ = gen_key(g_vars,p_vars,m)
print sorted(d_.items(), key=operator.itemgetter(1))

p_ = [p_d['REST'],p_d['FANDUEL_SALARY'],p_d['DRAFTKINGS_SALARY'],p_d['MATCHUP'],p_d["FANT_PREDICTION"],p_d["POSITION"],p_d['FANT_TARGET']]


for t_name in np.unique(teams[:,t_d['TEAM_NAME_SEL']].astype(str)):
    team_players = players[players[:,p_d['TEAM_NAME']].astype(str) == t_name]
    team_games   = teams[teams[:,t_d["TEAM_NAME_SEL"]].astype(str) == t_name]

    for game in team_games:
        gid = game[t_d['GAME_ID_SEL']]
        for player in team_players[team_players[:,p_d['GAME_ID']] == gid]:
            event = []
            g_vars = np.append( np.append(map(lambda x: t_d[x], ['AVG_' + s + "_SEL" for s in np.array(m.t_inclusive).astype(str)]) ,
                                          map(lambda x: t_d[x], ['AVG_' + s + "_OPP" for s in np.array(m.t_inclusive).astype(str)]) ),
                               map(lambda x: t_d[x] ,["AVG_" + str(s) + "_" + player[p_d['POSITION']] + "_OPP" for s in m.t_fint]))

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


param_1     = {'max_depth':3,'eta':.05, 'silent':1,'subsample' : .5,'colsample_bytree':.5}#, #,'colsample_bytree':.75,'gamma':100,'min_child_weight':100}
num_round   = 60
bst_1         = xgb.train(param_1,dtrain_,num_round,watchlist, feval=evalerror)
preds_        = bst_1.predict(dvalid_)
mean_1 ,mean_2,counter_1= 0,0,0
x,y,z = [],[],[]
yp,zp = [],[]
for id_,line in enumerate(events[int(.9*len(events)):]):
    if float(line[d_["AVG_5"]]) != float(line[d_["AVG_5"]]):
        continue
    mean_1 += np.power((float(line[d_["FANT_TARGET"]]) - float(line[d_["FANT_PREDICTION"]])),2) #np.abs(float(line[d_["FANT_TARGET"]]) - float(line[d_["FANT_PREDICTION"]]))/(1.0 + line[d_["FANT_TARGET"]])
    mean_2 += np.power((float(line[d_["FANT_TARGET"]]) - preds_[id_]),2)#np.abs(float(line[d_["FANT_TARGET"]])- preds_[id_])/(1.0 + line[d_["FANT_TARGET"]])
    y.append(np.power((float(line[d_["FANT_TARGET"]]) - preds_[id_]),2))#np.abs(float(line[d_["FANT_TARGET"]])- preds_[id_]))
    z.append(np.power((float(line[d_["FANT_TARGET"]]) - float(line[d_["FANT_PREDICTION"]])),2))#np.abs(float(line[d_["FANT_TARGET"]])- float(line[d_["FANT_PREDICTION"]])))
    yp.append(np.abs(float(line[d_["FANT_TARGET"]])- preds_[id_])/(line[d_["FANT_TARGET"]] + 1))
    zp.append(np.abs(float(line[d_["FANT_TARGET"]])- float(line[d_["FANT_PREDICTION"]]))/(line[d_["FANT_TARGET"]] + 1))
    x.append(line[d_["FANT_PREDICTION"]])
    counter_1 = counter_1 + 1
import matplotlib.pyplot as plt
fig, ax = plt.subplots( nrows=1, ncols=2 )

fig, axs = plt.subplots( nrows=2, ncols=2 )

axs[0, 0].scatter(x, y,color="red")
axs[0, 0].set_title("M.L. Predictions " )

axs[0, 1].scatter(x, z,color="blue")
axs[0, 1].set_title("Internet Predictions " )



axs[1, 0].scatter(x, np.log(np.array(yp)+1.0),color="red")
axs[1, 0].set_title("M.L. Predictions (MAPE)" )

axs[1, 1].scatter(x, np.log(np.array(zp)+1.0),color="blue")
axs[1, 1].set_title("Internet Predictions (MAPE) " )

fig.savefig('foo.png')


mean_1 = np.sqrt(mean_1)/counter_1
mean_2 = np.sqrt(mean_2)/counter_1
print mean_1,mean_2
