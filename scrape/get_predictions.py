##It's pretty slow due to the time to load each URL, but it works.
import urllib2
from bs4 import BeautifulSoup
import re
import datetime
import numpy as np
import string
import csv
import pickle

dict = {}
bad_chars = '@^(){}[]<>'
for year in range(2014,2017):
    for mon in range(1,13):
        print year,mon
        for day in range(1,32):
            for pred in ['fd','dd','dk','sf']:

                url = 'http://rotoguru1.com/cgi-bin/hyday.pl?mon=%s&day=%s&year=%s&game=%s' % (mon,day,year,pred)
                page = urllib2.urlopen(url).read()
                soup = BeautifulSoup(page)
                date = (datetime.datetime(year=year, month=mon, day=day) - \
                        datetime.datetime(year=1970, month=1, day=1)).days

                try:
                    table = soup.find('table')

                    x = (len(table.findAll('tr')) - 1)
                    for row in table.findAll('tr')[1:x]:
                        if '$' not in str(row):
                            continue
                        col = row.findAll('td')
                        fixed_col = []

                        for id_,line in enumerate(col):
                            fixd_ = (re.sub(r'<.*?>', '', str(line)))
                            fixed_col.append(fixd_.translate(string.maketrans("", "", ), bad_chars))
                        if fixed_col[1] not in dict.keys():
                            dict[fixed_col[1]] = {}

                        if date not in dict[fixed_col[1]].keys():
                            dict[fixed_col[1]][date] = [fixed_col[3]]
                        else:
                            new_vec = np.append(np.copy(dict[fixed_col[1]][date]),fixed_col[3])
                            if len(new_vec) == 4:
                                pt_ind = fixed_col[8].find('pt')
                                pts    = fixed_col[8][pt_ind-2:pt_ind]
                                dict[fixed_col[1]][date] = np.append(new_vec,pts)
                                print fixed_col[1],date,dict[fixed_col[1]][date]
                            else:
                                dict[fixed_col[1]][date] = new_vec
                except:
                    print "the date %s-%s%s did not load" % (year,mon,day)
with open('pdick.pickle', 'wb') as handle:
  pickle.dump(dict, handle)

with open('pdick.pickle', 'rb') as handle:
  b = pickle.load(handle)

out_arr = []
for key_1 in b.keys():
    out_arr.append(np.append(key_1,b[key_1][16471]))
out_arr = np.array(out_arr)
print out_arr[out_arr[:,-1].argsort()]
