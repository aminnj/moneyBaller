import numpy as np
import pickle, gzip
from collections import Counter

np.set_printoptions(linewidth=205,formatter={'float_kind':lambda x: "%.2f" % x })

with gzip.open("../data/pickle/player_stats_2013.pkl","rb") as fh:
    data_raw = pickle.load(fh)

data = {}
for (pid,year),player in data_raw.items():
    weight, height, position = player["weight"], player["height"], player["position"]
    if type(weight) == type(unicode("")) or type(height) == type(unicode("")) or len(position) < 1: continue
    data[(pid,year)] = player


counter = Counter()
for (pid,year),player in data.items():
    for st in np.unique(player["stats"]["SHOT_TYPE"]): counter[st] += 1

N=12
for common in counter.most_common(N): print common
mostcommon = [mc[0] for mc in counter.most_common(N)]

for (pid,year),player in data.items()[:1]:
    weight, height, position = player["weight"], player["height"], player["position"]
    if type(weight) == type(unicode("")) or type(height) == type(unicode("")) or len(position) < 1:
        continue

    allexist = True
    for st in mostcommon:
        if st not in np.unique(player["stats"]["SHOT_TYPE"]):
            allexist = False
            break
    if not allexist: continue

    stats = []
    stats = player["stats"][np.vectorize(lambda x: x in mostcommon)(player["stats"]["SHOT_TYPE"])]
    stats = stats[stats["SHOT_TYPE"].argsort()]
    for stat in stats:
        print stat
    # stats = stats[stats[:,0].argsort()]

    vec = np.append(np.array([weight, height]), player["stats"]["FGA_FREQUENCY"])
    print vec

