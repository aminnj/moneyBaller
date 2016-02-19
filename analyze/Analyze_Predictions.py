import numpy as np
import xgboost as xgb
from sklearn.preprocessing import StandardScaler,Imputer
from sklearn import datasets, linear_model

def evalerror(preds, dtrain):
            labels  = dtrain.get_label()
            error_ = np.mean(    np.abs( labels[preds > 15] - preds[preds > 15]))
            return 'error, ' , float(error_)
def gen_dict(header):
    splitter_ = header[2:].split(",")
    d_ = {}
    for id_,line in enumerate(splitter_):
        d_[line] = id_
    return d_

f_events      = '../data/parsed/events.csv'
events        = np.genfromtxt(f_events, delimiter=",", filling_values=-999999, skip_header=1)

with open(f_events, 'r') as f:
    header = f.readline()
d_ = gen_dict(header)

print d_.keys()
X       = events[:,range(0,len(events[0])-1)]
y       = events[:,len(events[0])-1]

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
param_1     = {'max_depth':4,'eta':.05, 'silent':1,'colsample_bytree':.85,'subsample' : .45}#,'colsample_bytree':.5}
num_round   = 70
bst_1         = xgb.train(param_1,dtrain_,num_round,watchlist, feval=evalerror)
preds_1        = bst_1.predict(dvalid_)

regr = linear_model.Lasso (alpha = 3.2)#LinearRegression()
train_ = Imputer(missing_values='NaN', strategy='mean', axis=0).fit_transform(train_)
valid_ = Imputer(missing_values='NaN', strategy='mean', axis=0).fit_transform(valid_)

regr.fit(train_, train_target)
preds_2 = regr.predict(valid_)
preds_ = (np.array(preds_1) + np.array(preds_2)) / 2.0
mean_1 ,mean_2,counter_1= 0,0,0
y_1,z_1,y_2,z_2,y_3,z_3 = [],[],[],[],[],[]
x               = []
for id_,line in enumerate(events[int(.9*len(events)):]):
    if float(line[d_["FANT_PREDICTION"]]) != float(line[d_["FANT_PREDICTION"]]):
        continue
    if float(preds_[id_]) != float(preds_[id_]):
        continue
    if preds_[id_] < 15:
        continue


    y_1.append(np.power((float(line[d_["FANT_TARGET"]]) - preds_[id_]),2))#np.abs(float(line[d_["FANT_TARGET"]])- preds_[id_]))
    z_1.append(np.power((float(line[d_["FANT_TARGET"]]) - float(line[d_["FANT_PREDICTION"]])),2))#np.abs(float(line[d_["FANT_TARGET"]])- float(line[d_["FANT_PREDICTION"]])))

    y_2.append(np.abs((float(line[d_["FANT_TARGET"]]) - preds_[id_])))#np.abs(float(line[d_["FANT_TARGET"]])- preds_[id_]))
    z_2.append(np.abs((float(line[d_["FANT_TARGET"]]) - float(line[d_["FANT_PREDICTION"]]))))#np.abs(float(line[d_["FANT_TARGET"]])- float(line[d_["FANT_PREDICTION"]])))


    y_3.append(np.abs(float(line[d_["FANT_TARGET"]])- preds_[id_])/(preds_[id_]))
    z_3.append(np.abs(float(line[d_["FANT_TARGET"]])- float(line[d_["FANT_PREDICTION"]]))/ line[d_["FANT_PREDICTION"]])
    x.append(preds_[id_])
    counter_1 = counter_1 + 1


import matplotlib.pyplot as plt
fig, axs = plt.subplots( nrows=3, ncols=1 ,figsize=(15,15))

red = axs[0].scatter(x, y_1,color="red",label='M.L.')
blue = axs[0].scatter(x, z_1,color="blue",label='Internet')
axs[0].legend(handles=[red,blue])
axs[0].set_title("Squared Error " )
axs[0].set_ylim([np.min(y_1),np.max(y_1)])
axs[1].set_title("Linear Error" )
axs[1].set_ylim([np.min(y_2),np.max(y_2)])
axs[1].scatter(x,y_2,color="red")
axs[1].scatter(x,z_2,color="blue")
axs[2].scatter(x,y_3,color="red")
axs[2].scatter(x,z_3,color="blue")
axs[2].set_title("MAPE" )
axs[2].set_ylim([np.min(y_3),np.max(y_3)])

fig.subplots_adjust(hspace=.35)

fig.savefig('error_plots.png')


print np.sqrt(np.mean(y_1)),np.sqrt(np.mean(z_1))
print np.mean(y_2),np.mean(z_2)
print np.mean(y_3),np.mean(z_3)
