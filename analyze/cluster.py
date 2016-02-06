import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pickle, gzip, sys
from collections import Counter
from sklearn import cluster
sys.path.insert(0,"../")
import utils.utils as u

np.set_printoptions(linewidth=205,formatter={'float_kind':lambda x: "%.2f" % x })

# some vars
year = 2013
N=12 # how many of the most common features to use for clustering
n_clusters=7

with gzip.open("../data/pickle/player_stats_%i.pkl" % year,"rb") as fh:
    data_raw = pickle.load(fh)

data = {}
for (pid,year),player in data_raw.items():
    # make new data object with players that have these basic ingredients filled out
    weight, height, position = player["weight"], player["height"], player["position"]
    # if player["position"] == "Center-Forward": player["position"] = "Forward-Center" # FIXME, do we want to relabel these?
    # if player["position"] == "Guard-Forward": player["position"] = "Forward-Guard" # FIXME, do we want to relabel these?
    if type(weight) == type(unicode("")) or type(height) == type(unicode("")) or len(position) < 1: continue
    data[(pid,year)] = player


counter = Counter()
# count which stat type shows up the most
for (pid,year),player in data.items():
    for st in np.unique(player["stats"]["SHOT_TYPE"]): counter[st] += 1

# print N most common stats
for common in counter.most_common(N): print common
mostcommon = [mc[0] for mc in counter.most_common(N)]

Xtot = []
for (pid,year),player in data.items():
    weight, height, position = player["weight"], player["height"], player["position"]
    if type(weight) == type(unicode("")) or type(height) == type(unicode("")) or len(position) < 1:
        continue

    allexist = True
    # requrie that this player has all of the N most common stats present
    # if even one is missing, then there's no way we can cluster, so we skip it
    # of course, we can change this so that we don't use the N most common
    # but we use oru own handpicked variables instead
    for st in mostcommon:
        if st not in np.unique(player["stats"]["SHOT_TYPE"]):
            allexist = False
            break
    if not allexist: continue

    # get selected stats and sort by stat name so that they are in a common order for clustering
    stats = []
    stats = player["stats"][np.vectorize(lambda x: x in mostcommon)(player["stats"]["SHOT_TYPE"])]
    stats = stats[stats["SHOT_TYPE"].argsort()]
    Xtot.append( np.append(np.array([pid, weight,height]),stats["FGA_FREQUENCY"]) )

Xtot = np.array(Xtot)
print Xtot

clust = cluster.KMeans(n_clusters=n_clusters, n_init=100, max_iter=500)
clust.fit(Xtot[:,1:])

# make a dictionary that takes a key and gives you a list of cluster labels for players that have that position
positions = np.unique(np.array([p["position"] for p in data.values()]))
dPositions = {position:[] for position in positions}
for pid, label in np.c_[Xtot[:,0], clust.labels_]:
    position = data[(int(pid),year)]["position"]
    dPositions[position].append(label)

fig = plt.figure()
ax = plt.subplot(111)
ax.hist([dPositions[p] for p in positions], n_clusters, histtype='bar', stacked=True, label=positions)
plt.ylabel('N')
plt.xlabel('Cluster label')
plt.title("Position composition of clusters")
box = ax.get_position()
ax.set_position([box.x0, box.y0, box.width * 0.7, box.height])
ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
fig.savefig("clusters.png")
u.web("clusters.png")
