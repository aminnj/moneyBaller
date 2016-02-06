##This still needs a few more tweaks.
import urllib2
from bs4 import BeautifulSoup
import re
import datetime
import numpy as np
import string
import csv

dict = {}
bad_chars = '@^(){}[]<>'
for year in range(2014,2017)[2:3]:
    for mon in range(1,13)[1:2]:
        for day in range(1,32)[4:5]:
            for pred in ['fd','dd','dk','sf']:
                url = 'http://rotoguru1.com/cgi-bin/hyday.pl?mon=%s&day=%s&year=%s&game=%s' % (mon,day,year,pred)
                page = urllib2.urlopen(url).read()
                soup = BeautifulSoup(page)
                date = (datetime.datetime(year=year, month=mon, day=day) - \
                        datetime.datetime(year=1970, month=1, day=1)).days

                #try:
                table = soup.find('table')

                x = (len(table.findAll('tr')) - 1)
                new_table = []
                for row in table.findAll('tr')[1:x]:
                    if '$' not in str(row):
                        continue

                    col = row.findAll('td')
                    fixed_col = []

                    for line in col:
                        fixd_ = (re.sub(r'<.*?>', '', str(line)))
                        fixed_col.append(fixd_.translate(string.maketrans("", "", ), bad_chars))

                    if fixed_col[1] not in dict.keys():
                        dict[fixed_col[1]] = {}
                        if date not in dict[fixed_col[1]].keys():
                            dict[fixed_col[1]][date] = [fixed_col[3]]
                            print dict[fixed_col[1]].keys()
                        else:
                            print 'else'
                            dict[fixed_col[1]][date] = np.append(dict[fixed_col[1]][date].copy,fixed_col[3])
                    #print len(dict[fixed_col[1]][date])
                print new_table
                #except:
                #    print 'table error'
