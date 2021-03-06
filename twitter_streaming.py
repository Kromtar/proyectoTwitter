from __future__ import print_function
from pymongo import MongoClient
from os.path import join, dirname
from dotenv import load_dotenv
import os
import tweepy
import json
import time

WORDS = []
FOLLOW = []

#Lee fichero externo
def readTxtTerms():
	f = open ('HashtagList.txt','r')
	mensaje = f.read()
	mensaje=mensaje.split("\n")
	global WORDS
	WORDS = [i for i in mensaje]

	f.close()

#StreamingListener
class StreamListener(tweepy.StreamListener):
    def on_connect(self):
        print("Conactado")

    def on_error(self, status_code):
        print('Error en streaming: ' + repr(status_code) + ' ,60 seg de pausa')
        time.sleep(60)

    def on_data(self, data):
        try:
			#Deja en formato
            datajson = json.loads(data)
            created_at = datajson['created_at']

			#No considera los Retweet
            if not datajson['text'].startswith('RT'):
				#Inserta en la db
                coll.insert(datajson)
                print("Tweet en: " + str(created_at))

        except Exception as e:
           print('Error en DB: ' + e)


if __name__ == '__main__':
	#Lee variables de entorno
    dotenv_path = join(dirname(__file__), 'Keys.env')
    load_dotenv(dotenv_path)

	#Se conecta a la db
    if(os.environ.get('DB_USER') == '' and os.environ.get('DB_PASS') == ''):
        uri = os.environ.get('DB_HOST')
    else:
        uri = 'mongodb://{}:{}@{}/{}'.format(os.environ.get('DB_USER'),os.environ.get('DB_PASS'),os.environ.get('DB_HOST'),os.environ.get('DB_NAME'))
    client = MongoClient(uri)
    db = client[os.environ.get('DB_NAME')]
    coll = db[os.environ.get('DB_COLLECTION')]

	#Configura la API de Twitter
    auth = tweepy.OAuthHandler(os.environ.get('TWITTER_CONSUMER_TOKEN'), os.environ.get('TWITTER_CONSUMER_SECRET'))
    auth.set_access_token(os.environ.get('TWITTER_ACCESS_KEY'), os.environ.get('TWITTER_ACCESS_SECRET'))
	#Configura rate limit y manejo de errores de conexion
    api=tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, retry_count=30, retry_delay=60, retry_errors=set([401, 403, 404, 420, 429, 500, 502, 503, 504]))

	#Lee la lista de amigos de la cuenta de Twitter
    friends = sorted(api.friends_ids())
    FOLLOW = list(map(str, friends))

	#Lee lista de hashtag
    readTxtTerms()

	#Inicia streaming
    listener = StreamListener()
    streamer = tweepy.Stream(auth=api.auth, listener=listener)
    print("Buscando terminos: " + str(WORDS))
    print("Siguiendo usuarios: " + str(FOLLOW))
    streamer.filter(follow=FOLLOW, track=WORDS, languages=["es"])
