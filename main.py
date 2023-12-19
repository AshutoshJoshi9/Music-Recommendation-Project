import requests
import base64
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split 
from sklearn.preprocessing import MinMaxScaler 
from datetime import datetime 
from sklearn.metrics.pairwise import cosine_similarity
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from functions import *
import PySimpleGUI as sg


client_ID = 'c0f9b7a154ff4cb6808b7f0337aa3e04'
client_secret = '1b108e0541f5463f9aae2c55f6d86f99'

client_credentials = f"{client_ID}:{client_secret}"
client_credentials_base64 = base64.b64encode(client_credentials.encode())

#request for token access
token_url = 'https://accounts.spotify.com/api/token'
headers = {'Authorization': f'Basic {client_credentials_base64.decode()}'}
data = {'grant_type': f'client_credentials'}
response = requests.post(token_url, data=data, headers=headers)


if response.status_code == 200:
    access_token = response.json()['access_token']
    print("Access token obtained.")
else:
    print("Error obtaining access token.")
    exit()



#function to get recs based on features
def content_based_recommendations(input_song_name, num_recommendations=5):
    if input_song_name not in music_df['Track Name'].values:
        print(f"{input_song_name} not found in playlist. Enter valid song name.")
        return
    
    #index of the input song in the music dataframe
    input_song_index = music_df[music_df['Track Name'] == input_song_name].index[0]

    # Calculate the similarity scores based on music features (cosine similarity)
    similarity_scores = cosine_similarity([music_features_scaled[input_song_index]], music_features_scaled)

    # Get the indices of the most similar songs
    similar_song_indices = similarity_scores.argsort()[0][::-1][1:num_recommendations + 1]

    # Get the names of the most similar songs based on content-based filtering
    content_based_recommendations = music_df.iloc[similar_song_indices][['Track Name', 'Artists', 'Album Name', 'Release Date', 'Popularity']]

    return content_based_recommendations


#function to get hybrid recommendations based on weighted popularity
def hybrid_recommendations(input_song_name, num_recommendations=5, alpha=0.5):
    if input_song_name not in music_df['Track Name'].values:
        print(f"'{input_song_name}' not found in the dataset. Please enter a valid song name.")
        return

    # Get content-based recommendations
    content_based_rec = content_based_recommendations(input_song_name, num_recommendations)

    # Get the popularity score of the input song
    popularity_score = music_df.loc[music_df['Track Name'] == input_song_name, 'Popularity'].values[0]

    # Calculate the weighted popularity score
    weighted_popularity_score = popularity_score * calc_weighted_popularity(music_df.loc[music_df['Track Name'] == input_song_name, 'Release Date'].values[0])

    # Combine content-based and popularity-based recommendations based on weighted popularity
    hybrid_recommendations = content_based_rec
    hybrid_recommendations = hybrid_recommendations.append({
        'Track Name': input_song_name,
        'Artists': music_df.loc[music_df['Track Name'] == input_song_name, 'Artists'].values[0],
        'Album Name': music_df.loc[music_df['Track Name'] == input_song_name, 'Album Name'].values[0],
        'Release Date': music_df.loc[music_df['Track Name'] == input_song_name, 'Release Date'].values[0],
        'Popularity': weighted_popularity_score
    }, ignore_index=True)

    # Sort the hybrid recommendations based on weighted popularity score
    hybrid_recommendations = hybrid_recommendations.sort_values(by='Popularity', ascending=False)

    # Remove the input song from the recommendations
    hybrid_recommendations = hybrid_recommendations[hybrid_recommendations['Track Name'] != input_song_name]


    return hybrid_recommendations



#GUI
sg.theme("DarkBlue14")

playlist_text = sg.InputText("", key='playlist', tooltip="Enter Playlist ID")
playlist_label = sg.Text("Enter Spotify Playlist Link: ")
input_song_text = sg.InputText("", key='song', tooltip="Enter exact song name.")
input_song_name_label = sg.Text("Enter exact name of song: ")
recommendations_button = sg.Button("Recommend", key='recommend', tooltip="Recommend")
recommendations_textbox = sg.Listbox(values="", key='recs', enable_events=True, size=[80, 10])

window = sg.Window("Song Reccommendations", layout=[[playlist_label, playlist_text], 
                                                    [input_song_name_label, input_song_text, recommendations_button], 
                                                    [recommendations_textbox]])

while True:
    event, values = window.read()

    match event:
        case 'recommend':
            input_song_name = values['song']
            
            if (input_song_name == "" or values['playlist'] == ""):
                sg.popup("Enter playlist link and song name first.")
            else:
                #to get data from playlist
                playlist_ID = values['playlist'][34: 56]
                print(playlist_ID)
                music_df = getTrendingPlaylistData(playlist_ID, access_token)
                #normalizing music features using min-max scaling
                scaler = MinMaxScaler()
                music_features = music_df[['Danceability', 'Energy', 'Key', 
                                            'Loudness', 'Mode', 'Speechiness', 'Acousticness',
                                            'Instrumentalness', 'Liveness', 'Valence', 'Tempo']].values

                music_features_scaled = scaler.fit_transform(music_features)

                try:
                    recommendations = hybrid_recommendations(input_song_name, num_recommendations=5)
                    print(f"Recommended songs for {input_song_name} are : ")
                    window["recs"].update(values=recommendations['Track Name']+"-- by "+recommendations['Artists'])
                    print(recommendations)
                except TypeError:
                    sg.popup("Please enter valid song name.", font=("Helvetica", 20))
        case sg.WIN_CLOSED:
            break
            
    print(event)
    print(values)

window.close()