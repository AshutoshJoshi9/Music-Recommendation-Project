import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split 
from sklearn.preprocessing import MinMaxScaler 
from datetime import datetime 
from sklearn.metrics.pairwise import cosine_similarity
import spotipy
from spotipy.oauth2 import SpotifyOAuth

def getTrendingPlaylistData(playlist_ID, access_token):
    sp = spotipy.Spotify(auth=access_token)

    playlist_tracks = sp.playlist_tracks(playlist_ID, fields='items(track(id, name, artists, album(id, name)))')

    #Extraction of relevant info storing it in a list
    music_data = []
    for track_info in playlist_tracks['items']:
        track = track_info['track']
        track_name = track['name']
        artists = ', '.join([artist['name'] for artist in track['artists']])
        album_name = track['album']['name']
        album_id = track['album']['id']
        track_id = track['id']

        #for audio features
        audio_features = sp.audio_features(track_id)[0] if track_id!='Not available' else None

        #release date
        try:
            album_info = sp.album(album_id) if album_id!='Not available' else None
            release_date = album_info['release_date'] if album_info else None
        except:
            release_date = None

        #for popularity of track
        try:
            track_info = sp.track(track_id) if track_id!='Not available' else None
            popularity = track_info['popularity']
        except:
            popularity = None
        
        #more track info
        track_data = {
            'Track Name': track_name,
            'Artists': artists,
            'Album Name': album_name,
            'Album ID': album_id,
            'Track ID': track_id,
            'Popularity': popularity,
            'Release Date': release_date,
            'Duration (ms)': audio_features['duration_ms'] if audio_features else None,
            'Explicit': track_info.get('explicit', None),
            'External URLs': track_info.get('external_urls', {}).get('spotify', None),
            'Danceability': audio_features['danceability'] if audio_features else None,
            'Energy': audio_features['energy'] if audio_features else None,
            'Key': audio_features['key'] if audio_features else None,
            'Loudness': audio_features['loudness'] if audio_features else None,
            'Mode': audio_features['mode'] if audio_features else None,
            'Speechiness': audio_features['speechiness'] if audio_features else None,
            'Acousticness': audio_features['acousticness'] if audio_features else None,
            'Instrumentalness': audio_features['instrumentalness'] if audio_features else None,
            'Liveness': audio_features['liveness'] if audio_features else None,
            'Valence': audio_features['valence'] if audio_features else None,
            'Tempo': audio_features['tempo'] if audio_features else None,
        }

        music_data.append(track_data)

    #To create a pandas dataframe from the list of dictionaries
    df = pd.DataFrame(music_data)

    return df


#function to calculate weighted popularity scores based on release date
def calc_weighted_popularity(release_date):
    release_date = datetime.strptime(release_date, '%Y-%m-%d')
    time_span = datetime.now() - release_date
    
    #weighted popularity score based on time span
    weight = 1 / (time_span.days + 1)
    return weight

