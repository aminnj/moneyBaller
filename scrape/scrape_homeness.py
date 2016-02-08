import bs4, requests, pickle, sys, json, time
import pprint
import numpy as np
from tqdm import tqdm

teams = {
"ATL": {"name": "Atlanta Hawks", "city": "Atlanta, GA"},
"BKN": {"name": "Brooklyn Nets", "city": "Brooklyn, NY"},
"BOS": {"name": "Boston Celtics", "city": "Boston, MA"},
"CHA": {"name": "Charlotte Bobcats", "city": "Charlotte, NC"},
"CHI": {"name": "Chicago Bulls", "city": "Chicago, IL"},
"CLE": {"name": "Cleveland Cavaliers", "city": "Cleveland, OH"},
"DAL": {"name": "Dallas Mavericks", "city": "Dallas, TX"},
"DEN": {"name": "Denver Nuggets", "city": "Denver, CO"},
"DET": {"name": "Detroit Pistons", "city": "Auburn Hills, MI"},
"GSG": {"name": "Golden State Warriors", "city": "Oakland, CA"},
"HOU": {"name": "Houston Rockets", "city": "Houston, TX"},
"IND": {"name": "Indiana Pacers", "city": "Indianpolis, IN"},
"LAC": {"name": "Los Angeles Clippers", "city": "Los Angeles, CA"},
"LAL": {"name": "Los Angeles Lakers", "city": "El Segundo, CA"},
"MEM": {"name": "Memphis Grizzlies", "city": "Memphis, TN"},
"MIA": {"name": "Miami Heat", "city": "Miami, FL"},
"MIL": {"name": "Milwaukee Bucks", "city": "Milwaukee, WI"},
"MIN": {"name": "Minnesota Timberwolves", "city": "Minneapolis, MN"},
"NOP": {"name": "New Orleans Pelicans", "city": "New Orleans, LA"},
"NYK": {"name": "New York Knicks", "city": "New York, NY"},
"OKC": {"name": "Oklahoma City Thunder", "city": "Oklahoma City, OK"},
"ORL": {"name": "Orlando Magic", "city": "Orlando, FL"},
"PHI": {"name": "Philadelphia 76ers", "city": "Philadelphia, PA"},
"PHX": {"name": "Phoenix Suns", "city": "Phoenix, AZ"},
"POR": {"name": "Portland Trail Blazers", "city": "Portland, OR"},
"SAC": {"name": "Sacramento Kings", "city": "Sacramento, CA"},
"SAC": {"name": "San Antonio Spurs", "city": "San Antonio, TX"},
"TOR": {"name": "Toronto Raptors", "city": "Toronto, ON"},
"UTA": {"name": "Utah Jazz", "city": "Salt Lake City, UT"},
"WAS": {"name": "Washington Wizards", "city": "Washington, DC"},
}

def get_lat_long(city):
    try:
        url = "http://maps.googleapis.com/maps/api/geocode/json?address=%s" % city
        data = requests.get(url)
        js = json.loads(data.text)
        location = js["results"][0]["geometry"]["location"]
        lat = float(location["lat"])
        lng = float(location["lng"])
    except:
        print "error getting coordinates for %s" % city
        return None, None
    return lat, lng

# print get_lat_long("Sacramento, CA")

# sys.exit()

states = ["AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"]

d = {}
d["players"] = {}

cities = []
cities.extend( [teams[k]["city"] for k in teams.keys()] )

# for state in tqdm(states[:1]):
for state in tqdm(states):
    url = "http://www.basketball-reference.com/friv/birthplaces.cgi?country=US&state=%s" % state
    data = requests.get(url).content
    bs = bs4.BeautifulSoup(data, "html.parser")
    for tr in bs.findAll('tr', {'class':''}):
        tds = tr.findAll('td')
        if len(tds) > 20:
            name = [td.text for td in tds][1].replace("*","")
            birthday = [td.text for td in tds][-2]
            city = [td.text for td in tds][-1]

            cities.append("%s, %s" % (city,state))

            if name in d["players"]: print "duplicate name: %s" % name
            d["players"][name] = (city,state,birthday)
        
cities = np.unique(np.array(cities))

d["cities"] = {}
# for city in tqdm(cities[:5]):
for city in tqdm(cities):
    time.sleep(0.3)
    d["cities"][city] = get_lat_long(city)


print d["cities"]

d["teams"] = {}
for abbr in teams:
    city = teams[abbr]["city"]
    name = teams[abbr]["name"]
    if city in d["cities"]:
        coords = d["cities"][city]
        d["teams"][abbr] = coords
        d["teams"][name] = coords

print "Scraped %i players from %i unique cities" % (len(d["players"]), len(d["cities"]))

with open("../data/pickle/hometown_distances.pkl","w") as fh:
    pickle.dump( d, fh )
