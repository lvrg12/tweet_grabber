import tweepy
import json
import datetime
from datetime import timedelta
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy.streaming import StreamListener
from textblob import TextBlob
from http.client import IncompleteRead # Python 3

import requests

# put twitter credentials below
consumer_key = 'TelkaEC2GUWR0IJogWxkrpZKy'
consumer_secret = 'ENYYJseZJ1IY0wqXUSnEj0i2L0Xz3v2c6MRvPEzY6hnrt3ZEEj'
access_token = '1620837440-0p8voswXhMYGO8upThRqeGwzUuh3TI9sPnQkZim'
access_secret = 'obvlWiW1Tvkdl1JYyA6hbIrJ96yvq1OS2hILRHs3R0HHy'

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)

api = tweepy.API(auth)


def read_counties():
    dict = {}
    with open("counties.txt","r+") as c:
        for line in c:
            code = line.rstrip()
            dict[code] = (0, 0)
    return dict

def write_counties(counties):
    with open("mapvalues.txt", "w+") as f:
        f.write("id\trate\n")
        for key, val in counties.items():
            f.write(key+"\t"+str(val[0])+"\n")

def clean_coordinates(tweet):
    longitude, latitude = (tweet["coordinates"]["coordinates"])  # extract coordinates from dictionary
    return str(latitude), str(longitude)

def clean_place(tweet):
    longitude, latitude = (tweet["place"]["bounding_box"]["coordinates"][0][0])
    return str(latitude), str(longitude)

def get_coordinates(json_data):
    if json_data['coordinates']:
        latitude, longitude = clean_coordinates(json_data)
        r = requests.get("http://www.datasciencetoolkit.org/coordinates2politics/" + latitude + "%2c" + longitude)
        return json.loads(r.text)

    elif json_data['place']:
        latitude, longitude = clean_place(json_data)
        r = requests.get("http://www.datasciencetoolkit.org/coordinates2politics/" + latitude + "%2c" + longitude)
        return json.loads(r.text)

    else:
        return ""

# prints tweet text, sentiment analysis
# county code and its current sentiment analysis average
def printFormat(text,sentiment,code,line):
    print("Text:\t\t\t",text)
    print("Sentiment:\t\t",sentiment)
    print("County Code:\t",code)
    print("(Avg, #):\t\t",line,"\n")

# returns sentiment analysis on input text
def getSentiment(text):
    textb = TextBlob(text)
    sentiment = 5 * float(textb.sentiment.polarity)
    return sentiment

# updates county code average on counties.txt
def updateCounty(code,sentiment):
    line = counties[code]
    avg = line[0]
    count = line[1]
    new_avg = (avg * count + sentiment) / (count + 1)
    counties[code] = (new_avg, count + 1)
    write_counties(counties)

counties = read_counties()

query = "trump"
today = datetime.datetime.now().date()
todayMinus7 = today - timedelta(days=7)

page_count = 0
for status in tweepy.Cursor(api.search, q=query, count=2, result_type="recent", lang='en', include_entities=True, since= todayMinus7, until= today).pages():
    for s in status:
        try:
            json_data = s._json
            r = get_coordinates(json_data)

            if r != "":
                for dict in r[0]['politics']:
                    if dict['type'] == 'admin6':
                        code = dict['code'].replace('_', '')
                        text = str(json_data['text'])
                        sentiment = getSentiment(text)
                        updateCounty(code, sentiment)
                        printFormat(text, sentiment, code, counties[code])

        except BaseException as e:
            # print("Error on_data: %s" % str(e))
            pass

    page_count += 1
    if page_count >= 40:
        break