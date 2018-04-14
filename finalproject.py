import requests
import json
import secrets
import sys
import sqlite3
import webbrowser

from flask import Flask, render_template
app = Flask(__name__)
CACHE_FNAME = 'finalproject.json'

try:
    conn=sqlite3.connect('finalproject.db')
except:
    print('failed to open.')
    sys.exit(1)
cur=conn.cursor()

def init_db():
    cur.execute('DROP TABLE IF EXISTS businesses')
    cur.execute('DROP TABLE IF EXISTS reviews')
    cur.execute('CREATE TABLE IF NOT EXISTS businesses (Id INTEGER PRIMARY KEY, name TEXT, lattitude REAL, longitude REAL, address TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS reviews (Id INTEGER PRIMARY KEY, rating REAL, price TEXT, primary_category TEXT, business_id INTEGER)')
    conn.commit()

def loadCache():
    try:
        cache_file = open(CACHE_FNAME, 'r')
        cache_contents = cache_file.read()
        CACHE_DICTION = json.loads(cache_contents)
        cache_file.close()
    except:
        CACHE_DICTION = {}
    return CACHE_DICTION

CACHE_DICTION = loadCache()

def params_unique_combination(baseurl, params):
    alphabetized_keys = sorted(params.keys())
    res = []
    for k in alphabetized_keys:
        res.append("{}-{}".format(k, params[k]))
    return baseurl + "_".join(res)
def make_request_using_cache(baseurl, params, headers={}):
    unique_ident = params_unique_combination(baseurl,params)
    if unique_ident in CACHE_DICTION:
        #print("Getting cached data...")
        return CACHE_DICTION[unique_ident]
    else:
        #print("Making a request for new data...")
        resp = requests.get(baseurl, params, headers=headers)
        CACHE_DICTION[unique_ident] = json.loads(resp.text)
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close()
        return CACHE_DICTION[unique_ident]

def getYelpData(searchTerm, placeName):
    raw_data_list = []
    for offset in range(0, 150, 50):
        f= make_request_using_cache('https://api.yelp.com/v3/businesses/search', params={
        'term': searchTerm, 'location': placeName, 'radius': 16000, "limit": 50, "offset": offset, "sort_by" : "distance"
        }, headers={'Authorization':'Bearer {}'.format(secrets.Yelp_API)})
        raw_data_list.extend(f['businesses'])
    return [Yelp(raw_data) for raw_data in raw_data_list]

class Yelp():
    def __init__(self, json):
        self.name=json['name']
        self.lattitude= json['coordinates']['latitude']
        self.longitude=json['coordinates']['longitude']
        self.address=' '.join(json['location']['display_address'])
        self.reviews=json['rating']
        self.price=json.get('price', "")
        try:
            self.primary_category=json['categories'][0]['title']
        except:
            self.primary_category="None"
    def __str__(self):
        return f"Adding {self.name} of type {self.primary_category} to the database!)"

def loadYelpData(yelpList):
    for yelp_inst in yelpList:
        #print(yelp_inst)
        cur.execute('INSERT INTO businesses VALUES (?,?,?,?,?)',(None, yelp_inst.name, yelp_inst.lattitude, yelp_inst.longitude, yelp_inst.address))
        cur.execute('SELECT Id FROM businesses WHERE name=?', (yelp_inst.name,))
        business_id=cur.fetchone()[0]
        cur.execute('INSERT INTO reviews VALUES (?,?,?,?,?)', (None, yelp_inst.reviews, yelp_inst.price, yelp_inst.primary_category, business_id))
    conn.commit()

def getHighestRated():
    cur.execute('SELECT name, rating, lattitude, longitude FROM businesses JOIN reviews ON businesses.Id=reviews.business_id WHERE rating>3.0 ORDER BY rating DESC LIMIT 5')
    top5 = cur.fetchall()
    top5 = [list(tup) + [index+1] for index,tup in enumerate(top5)]
    return top5

def getLowestRated():
    cur.execute('SELECT name, rating, lattitude, longitude FROM businesses JOIN reviews ON businesses.Id=reviews.business_id WHERE rating<=3.0 ORDER BY rating ASC LIMIT 5')
    bottom5 = cur.fetchall()
    bottom5 = [list(tup) + [index+1] for index,tup in enumerate(bottom5)]
    return bottom5

def getHighPrice():
    cur.execute('SELECT name, rating, lattitude, longitude, price FROM businesses JOIN reviews ON businesses.Id=reviews.business_id WHERE LENGTH(price)>2 ORDER BY price DESC LIMIT 5')
    pricey5 = cur.fetchall()
    pricey5 = [list(tup) + [index+1] for index,tup in enumerate(pricey5)]
    return pricey5

def getLowestPrice():
    cur.execute('SELECT name, rating, lattitude, longitude, price FROM businesses JOIN reviews ON businesses.Id=reviews.business_id WHERE LENGTH(price)<=2 AND Price != "" ORDER BY price ASC LIMIT 5')
    cheap5 = cur.fetchall()
    cheap5 = [list(tup) + [index+1] for index,tup in enumerate(cheap5)]
    return cheap5


if __name__ == "__main__":
    init_db()
    user=input('enter a search term: ')
    place=input('enter the name of a location: ')

    raw_data = getYelpData(user, place)
    # load data into database
    loadYelpData(raw_data)


    # High rating
    top5 = getHighestRated()

    @app.route("/highrating")
    def highrating():
        print("\n", "-"*20, "Highest Rated Restaurants and Bars", "-"*20)
        for rest in top5:
            print("{}. {} w/ {} stars.".format(rest[4], rest[0], rest[1]))

        return render_template('highrating.html', apikey=secrets.Google_API, centerLat=top5[0][2], centerLong=top5[0][3], top5=top5)


    # Low rating
    bottom5 = getLowestRated()

    @app.route("/lowrating")
    def lowrating():
        print("\n", "-"*20, "Worst Rated Restaurants and Bars", "-"*20)
        for rest in bottom5:
            print("{}. {} w/ {} stars.".format(rest[4], rest[0], rest[1]))

        return render_template('lowrating.html', apikey=secrets.Google_API, centerLat=bottom5[0][2], centerLong=bottom5[0][3], bottom5=bottom5)

    # High Price
    pricey5 = getHighPrice()

    @app.route("/highprice")
    def highprice():
        print("\n", "-"*20, "Most Expensive Restaurants and Bars", "-"*20)
        for rest in pricey5:
            print("{} -- {}. {} w/ {} stars.".format(rest[5], rest[4], rest[0], rest[1]))

        return render_template('expensive.html', apikey=secrets.Google_API, centerLat=pricey5[0][2], centerLong=pricey5[0][3], expensive5=pricey5)

    # Low Price
    cheap5 = getLowestPrice()

    @app.route("/cheapprice")
    def cheapprice():
        print("\n", "-"*20, "Least Expensive Restaurants and Bars", "-"*20)
        for rest in cheap5:
            print("{} -- {}. {} w/ {} stars.".format(rest[5], rest[4], rest[0], rest[1]))

        return render_template('cheap.html', apikey=secrets.Google_API, centerLat=cheap5[0][2], centerLong=cheap5[0][3], cheap5=cheap5)

    print(
    """
    - For highest rated restaurants and bars, open: localhost:3000/highrating
    - For worst rated restaurants and bars, open: localhost:3000/lowrating
    - For most expensive restaurants and bars, open: localhost:3000/highprice
    - For cheapest restaurants and bars, open: localhost:3000/cheapprice

    To stop the program and/or enter new search terms, press the Control & C keys.
    """)
    app.run(host= '0.0.0.0', port=3000)
