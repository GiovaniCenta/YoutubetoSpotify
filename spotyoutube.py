#Goal of this project is to make a song that we like on youtube go directly to our spotify "liked youtube songs" playlist
""" STEPS
1 - Log into youtube
2 - Grab our playlist
3 - Create a new playlist
4 - Search the song
5 - Add the song to the spotify playlist

"""
import json
import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import requests
import youtube_dl

from exceptions import ResponseException
from userData import spotyId,spotyToken
scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
from youtube_title_parse import get_artist_title

#print(spotifyUser.token)


class CreatePlaylist:
    
    def __init__(self):
        
        #self.youtube_client = self.yt_client()
        self.all_song_info = {}
        
    
    #1 - Log into youtube
    def yt_client(self):
         # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret.json"

        # Get credentials and create an API client
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()

        # from the Youtube DATA API
        youtube_client = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        return youtube_client
    
    #2 - Grab our playlist
    def get_ytplaylist(self):

        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret.json"

        # Get credentials and create an API client
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()
        youtube = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            maxResults=25,
            playlistId="PLQ_99qrIfCg3Mm7SDtxHfIBMt7aUkIDZD"
        )
        response = request.execute()

        for item in response["items"]:
           
            video_title = item["snippet"]["title"]
            youtube_url = "https://www.youtube.com/watch?v={}".format(
                item["id"])
            print("\n\n\n")
            #print(video_title)
            #print(youtube_url)
            
            # use youtube_dl to collect the song name & artist name
            #video = youtube_dl.YoutubeDL({}).extract_info(
                #'https://www.youtube.com/watch?v=dPhwbZBvW2o', download=False)
            artist, title = get_artist_title(video_title)
            #print(artist)
            #print(title)

            if title is not None and artist is not None:
                # save all important info and skip any missing song and artist
                self.all_song_info[video_title] = {
                    "youtube_url": youtube_url,
                    "song_name": title,
                    "artist": artist,

                    # add the uri, easy to get song to put into playlist
                    "spotify_uri": self.search_song(title, artist)

                }
            

            

        #print(response)
        print("\n\n\n")
        #print(video_title)


    
    
    
    #3 - Create a new playlist
    def new_spotifyplaylist(self):

        request_body = json.dumps({
            "name": "Youtube to Spotify playlist",
            "description": "Playlist of a program that I did in python that picks my songs from a youtube playlist, search them and add to this playlist :) ",
            "public": True
        })
        print(request_body)

        query = f"https://api.spotify.com/v1/users/{spotyId}/playlists"
        response = requests.post(
            url=query,
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {spotyToken}"
            }
        )
        print(response)
        response_json = response.json()

        # playlist id
        return response_json["id"]
        
        

    
    #4 - Search the song
    def search_song(self,song,artist):
        query = "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track&offset=0&limit=20".format(
            song,
            artist
        )
        response = requests.get(
            query,
            headers={
                "Content-Type":"application/json",
                "Authorization":"Bearer {}".format(spotyToken)
            }
        )

        
        response_json = response.json()
        
        songs = response_json["tracks"]["items"]
        #first song only
        uri = songs[0]["uri"]
        return uri
    
    #5 - Add the song to the spotify playlist
    def add_song(self):
         # populate dictionary with our liked songs
        self.get_ytplaylist()

        # collect all of uri
        uris = [info["spotify_uri"]
                for song, info in self.all_song_info.items()]

        # create a new playlist
        playlist_id = self.new_spotifyplaylist()

        # add all songs into new playlist
        request_data = json.dumps(uris)

        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(
            playlist_id)

        response = requests.post(
            query,
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotyToken)
            }
        )
        # check for valid response status
        if response.status_code != 201:
            raise ResponseException(response.status_code)

        response_json = response.json()
        return response_json

if __name__ == '__main__':
    cp = CreatePlaylist()
    cp.add_song()
    
    
    
    
    
    
    
    
    
    