import requests
import urllib2
import pandas as pd
import numpy as np
import time
from tqdm import tqdm

def get_game_url(shorturl):
    req = urllib2.Request(shorturl)
    res = urllib2.urlopen(req).geturl()
    return res

df = pd.DataFrame.from_csv("fanduelhistory.csv")

newlinks = ["" for _ in range(len(df))] # new column
for ilink,link in tqdm(enumerate(df["Link"][:3])):
    try: newlinks[ilink] = get_game_url(link)
    except: pass
    time.sleep(2)

df["GameLink"] = newlinks # add new column

df.to_csv("fanduelhistory_out.csv")
