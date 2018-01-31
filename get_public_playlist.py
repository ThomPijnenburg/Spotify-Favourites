# this script is to be executed in command line
# python get_public_playlist.py --playlist=SPOTIFY_PLAYLIST_URI


import argparse
import pprint
import sys
import os
import subprocess
import configparser
import json
import spotipy
import spotipy.util as util
import pandas as pd


import spotipy.oauth2 as oauth2

# client_credentials_manager = SpotifyClientCredentials()

def get_playlist_content(sp, user_id, playlist_id):
    if (playlist_id == None):
        print('Please define a playlist id with --playlist="ID_HERE"')
        return

    offset = 0
    songs = []
    while True:
        content = sp.user_playlist_tracks(user_id, playlist_id=playlist_id, fields=None, limit=100, offset=offset, market=None)
        songs += content['items']
        if content['next'] is not None:
            offset += 100
        else:
            break

    with open('{}-{}'.format(user_id, playlist_id), 'w') as outfile:
        json.dump(songs, outfile)

def get_user_playlists(sp):
    playlists = sp.current_user_playlists()

    for playlist in playlists['items']:
        print("Name: {}, Number of songs: {}, Playlist ID: {} ".
              format(playlist['name'].encode('utf8'),
                     playlist['tracks']['total'],
                     playlist['id']))

def get_playlist_audio_features(sp, user_id, playlist_id):
    offset = 0
    songs = []
    items = []
    ids = []
    while True:
        content = sp.user_playlist_tracks(user_id, playlist_id, fields=None, limit=100, offset=offset, market=None)
        songs += content['items']
        if content['next'] is not None:
            offset += 100
        else:
            break

    for i in songs:
        ids.append(i['track']['id'])

    index = 0
    audio_features = []
    while index < len(ids):
        audio_features += sp.audio_features(ids[index:index + 50])
        index += 50

    features_list = []
    for features in audio_features:

        features_list.append([features['id'],features['energy'], features['liveness'],
                              features['tempo'], features['speechiness'],
                              features['acousticness'], features['instrumentalness'],
                              features['time_signature'], features['danceability'],
                              features['key'], features['duration_ms'],
                              features['loudness'], features['valence'],
                              features['mode'], features['type'],
                              features['uri']])

    df = pd.DataFrame(features_list, columns=['id', 'energy', 'liveness',
                                              'tempo', 'speechiness',
                                              'acousticness', 'instrumentalness',
                                              'time_signature', 'danceability',
                                              'key', 'duration_ms', 'loudness',
                                              'valence', 'mode', 'type', 'uri'])
    df.to_csv('{}-{}.csv'.format(user_id, playlist_id), index=False)


def main(username, playlist):
    print('Performing authentication...')
    config = configparser.ConfigParser()
    config.read('config.cfg')
    SPOTIPY_CLIENT_ID = config.get('SPOTIFY', 'CLIENT_ID')
    SPOTIPY_CLIENT_SECRET = config.get('SPOTIFY', 'CLIENT_SECRET')
    SPOTIPY_REDIRECT_URI = config.get('SPOTIFY', 'REDIRECT_URI')
    SPOTIPY_PLAYLIST_ID = config.get('SPOTIFY', 'PLAYLIST_ID')

    scope = 'playlist-read-private'

    token = util.prompt_for_user_token(username, scope, client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI)

    if token:
        sp = spotipy.Spotify(auth=token)

        current_user= sp.current_user()

        print('Getting user\'s playlists...')
        get_user_playlists(sp)

        print('Getting playlist content...')
        get_playlist_content(sp, current_user['id'], playlist)

        print('Getting playlist audio features...')
        get_playlist_audio_features(sp, current_user['id'], playlist)
    else:
        print( "Can't get token for", username)


if __name__ == '__main__':
    print('Starting...')
    parser = argparse.ArgumentParser(description='description')
    parser.add_argument('--username', help='username')
    parser.add_argument('--playlist', help='playlist')
    args = parser.parse_args()
    main(args.username, args.playlist)