from __init__ import app, cur, conn
from flask import render_template, redirect, request
import requests
import datetime
import sys
from bs4 import BeautifulSoup
import urllib2

url = 'http://fa16-cs411-47.cs.illinois.edu'


@app.route('/', methods=['GET', 'POST'])
def welcome_user():
    if request.method == 'GET':
        return render_template('webpage2/welcome-form/welcome.html')
    else:
	username = request.form.get('username', None)
        password = request.form.get('password', None)
        if request.args.get("login", None):
            valid_login = username and password and authenticated(username, password)
            if valid_login:
                return redirect(url + "/{}/search".format(username))
            else:
                return render_template('webpage2/welcome-form/welcome.html', login_failed=True)

        elif request.args.get("signup", None):
            name = request.form.get('name', None)
            valid_signup = username and password and name and create_user(username, password, name)
            if valid_signup:
                return redirect(url + "/{}/search".format(username))
            else:
                return render_template('webpage2/welcome-form/welcome.html', login_failed=True)


@app.route('/<username>/logout')
def logout_user(username):
    change_user_logged_in(username, False)
    return redirect(url)


@app.route('/<username>/search')
def search(username):
    if not authenticated(username):
        return redirect(url)

    return render_template('webpage2/search.html', username=username)


@app.route('/example_query')
def example_query():
    cur.execute("SELECT page_title FROM page WHERE page_title LIKE '%Republic%'")
    query_name = "SELECT page_title FROM page WHERE page_title LIKE '%Republic%'"
    query = str(cur.fetchall())
    return render_template('example_query.html', query_name=query_name, query=query)


@app.route('/<username>/search/<keyword>/<lpnum>', methods=['GET'])
def get_trip(username, keyword, lpnum):
    if not authenticated(username):
        return render_templated('webpage2/welcome-form/welcome.html', login_failed=True)

    location1 = cur.execute("SELECT * FROM Location WHERE Name='Martinique'")
    location1 = list(cur.fetchone())
    location1.append("http://www.airtransat.com/getmedia/8304aca5-8ca0-4aa0-976d-cf11442d7871/Fort-de-France-thumbnail.jpg?width=515")
    location2 = cur.execute("SELECT * FROM Location WHERE Name='Nicaragua'")
    location2 = list(cur.fetchone())
    location2.append('http://servicesaws.iadb.org/wmsfiles/images/0x0/nicaragua-32899.jpg')
    location3 = cur.execute("SELECT * FROM Location WHERE Name='Thailand'")
    location3 = list(cur.fetchone())
    location3.append('http://newmedia.thomson.co.uk/live/vol/0/921d4b57639916341dfa76e38310ff7bc13b11e2/1080x608/web/ASIAFAREASTTHAILANDTHAILANDDES_000423KHAOLAKRES_002378.jpg')
    location4 = cur.execute("SELECT * FROM Location WHERE Name='Samoa'")
    location4 = list(cur.fetchone())
    location4.append('https://lonelyplanetimages.imgix.net/mastheads/GettyImages-167450923_full.jpg?sharp=10&vib=20&w=1200')
    location5 = cur.execute("SELECT * FROM Location WHERE Name='Panama'")
    location5 = list(cur.fetchone())
    location5.append('http://www.total.com/sites/default/files/styles/carrefour/public/thumbnails/image/panama.jpg')

    trip = [location1, location2, location3, location4, location5]
    coords = []
    for location in trip:
        coords.append(get_location_coords(location))
    trip = [location_to_dict(location) for location in trip]

    '''if not trip: 
        trip = [location1, location2, location3, location4, location5]
        for location in trip:
	    cur.execute('INSERT INTO TripLocation (Trip, location_name) VALUES (\"{}\",\"{}\")'.format(keyword, location[4]))
	    conn.commit()
    trip = get_trip_by_keyword(keyword)
    if trip:
        locations = get_trip_locations(keyword)
    else:
        possible_locations = get_best_locations(keyword)
        best_location = locations[lpnum]
        trip = create_trip(keyword, best_location, username)
    '''

    trip = get_best_locations(keyword)
    return render_template('webpage2/trip.html', trip=trip, coords=coords, keyword=keyword, liked=False)


@app.route('/<username>/search/<keyword>/<lpnum>/<like>')
def like_trip(username, keyword, lpnum, like):
    like = bool(like)
    curr.execute('''
                UPDATE TripAssessment
                SET Assessment={}
                WHERE TripKeyword='{}' AND Username='{}' AND LPNum={}
                '''.format(like, keyword, username, lpnum))

    conn.commit()

@app.route('/user_profile')
def get_user_profile():
    return render_template('webpage/user.html', user="Jeff")


def authenticated(username, password=None):
    user = get_user_by_username(username)
    if not user:
        return False

    user_password = user[1]
    logged_in = user[3]

    if not password and logged_in:
        return True
    elif user_password == password:
        change_user_logged_in(username, True)
        return True
    else:
        return False


def get_best_locations(keyword):
    '''
    Make requests to LostVoyager API with the user inputted keyword
    Choose most popular locations from request
    Return information needed to make trip and location AND IMAGE URL
    '''

    destinations = []

    keyword = urllib2.quote(keyword)
    url = "https://www.viator.com/search/"+keyword
    response = urllib2.urlopen(url)
    soup=BeautifulSoup(response.read(), "lxml")

    content = soup.find_all("p", class_="man mts note xsmall")
    for c in content:
        result = str(c)
        result = result[result.index(',')+2:]
        result = result[:result.index('<')-1]
        destinations.append(result)
       
    return destinations


def get_trip_locations(keyword):
    cur.execute("SELECT * FROM TripLocations WHERE TripKeyword='{}'".format(keyword))
    trip_locations = cur.fetchall()
    locations = [get_location_by_name(tr[1]) for tr in trip_locations]
    return locations


def get_trip_by_keyword(keyword):
    cur.execute("SELECT * FROM Trip WHERE Keyword='{}'".format(keyword))
    trip = cur.fetchone()
    return trip


def get_location_coords(location_name):
    rv = requests.get('http://maps.googleapis.com/maps/api/geocode/json?address={}&key=AIzaSyCoIJcakxVen5qGdu_PsV_ajdl33qwGskI'.format(location_name))
    data = rv.json()
    coords = data['results'][0]['geometry']['location']
    return (coords['lat'], coords['lng'])


def create_location_image(location_name):
    cur.execute("SELECT * FROM Photo WHERE LocationName='{}'".format(location_name)
    if cur.fetchone():
        return

    key = 'AIzaSyCoIJcakxVen5qGdu_PsV_ajdl33qwGskI'
    rv = requests.get('https://maps.googleapis.com/maps/api/place/autocomplete/json?key={}&input={}&type=geocode&'.format(key, query))
    data = rv.json()
    if data['status'] != 'OK':
        return None

    location = data['predictions'][0]
    place_id = location['place_id']
    rv = requests.get('https://maps.googleapis.com/maps/api/place/details/json?key={}&placeid={}'.format(key, place_id))
    data = rv.json()['result']
    photo_ref = data['photos'][0]['photo_reference']
    url = 'https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={}&key={}'.format(photo_ref, key)

    cur.execute("INSERT INTO Photo VALUES ('{}', '{})".format(location_name, url))
    conn.commit()


def get_location_by_name(name):
    cur.execute('''
                SELECT l.Description, l.Eat, l.See, l.Do, l.Name, p.URL
                FROM Location l, Photo p
                WHERE l.Name='{}' AND p.LocationName = '{}'
                '''.format(name))
    location = cur.fetchone()

    if location:
        return location_to_dict(location)
    return None


def get_location_by_coords(coords):
    cur.execute("SELECT * FROM Location WHERE Coordinates='{}'".format(coords))
    location = cur.fetchone()
    return location


def create_trip_location(keyword, location_name):
    cur.execute("INSERT INTO TripLocation VALUES ('{}','{}')".format(keyword, location_name))
    conn.commit()


def create_trip_user(keyword, username, lpnum):
    cur.execute("INSERT INTO TripUser VALUES ('{}','{}',{})".format(keyword, username, lpnum))
    conn.commit()


def create_user(username, password, name):
    user = get_user_by_username(username)
    if user:
        return False
    else:
        cur.execute("INSERT INTO User VALUES ('{}', '{}', '{}', '{}')".format(username, password, name, True))
	conn.commit()
        return True


def get_user_by_username(username):
    cur.execute("SELECT * FROM `User` WHERE Username='{}'".format(username))
    return cur.fetchone()


def change_user_logged_in(username, logged_in):
    cur.execute("UPDATE User SET LoggedIn={} WHERE Username='{}'".format(logged_in, username))
    conn.commit()


def create_trip(keyword, location_name, user):
    '''
    Create trip from location's go next
    '''

    # Get all associated go nexts with location
    cur.execute('''
                SELECT next_name, next_coords
                FROM Location Go Next
                WHERE source_name={}
                '''.format(location_name))
    rv = cur.fetchall()
    if not rv:
        raise ValueError('Location {} does not exist'.format(location_name))

    create_location_image(location_name)
    # Get info and create location for all go nexts
    for location in rv:
        name = location[0]
        coords = location[1]
        create_trip_location(keyword, name)
        create_location_image(name)

    # Create trip
    create_trip_user(keyword, user, lpnum)
    cur.execute('''
                INSERT INTO Trip
                VALUES ('{}', '{}')
                '''.format(keyword, location_name))

    trip = [get_location_by_name(location[0]) for location in rv]
    trip.append(get_location_by_name(location_name))
    return trip


def location_to_dict(location):
    location_dict = {'description':location[0],'eat':location[1],
                     'see':location[2], 'do':location[3],
                     'name':location[4], 'photo':location[5]}
    return location_dict
