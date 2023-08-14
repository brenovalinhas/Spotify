import requests
from requests.auth import HTTPBasicAuth
import urllib.parse
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import re
from unidecode import unidecode
import json

class SpotifyAPI:
    def __init__(self, client_id, client_secret, redirect_uri, access_token=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token = access_token

    def build_authorization_url(self) -> str:
        base_url = "https://accounts.spotify.com/authorize"
        query_params = urllib.parse.urlencode({
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": ""  # specify the scopes your application needs, separated by spaces
        })
        return f"{base_url}?{query_params}"

    def get_access_token(self, authorization_code: str) -> str:
        token_url = "https://accounts.spotify.com/api/token"
        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": self.redirect_uri
        }
        auth = HTTPBasicAuth(self.client_id, self.client_secret)
        response = requests.post(token_url, data=data, auth=auth)
        self.access_token = response.json().get('access_token')
        return self.access_token

    
    # Now you can use the access token to make authorized API requests
    def get_track_info(self, track: str, artist: str) -> dict:
        # Define the endpoint URL
        base_url = "https://api.spotify.com/v1/search"
        
        # Define the headers for authorization
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        # Define the query parameters
        params = {
            "q": f"track:{track} artist:{artist}",
            "type": "track",
            "limit": 1
        }
        
        # Make the GET request to the Spotify API
        response = requests.get(base_url, headers=headers, params=params)
        
        # Parse the JSON response
        json_response = response.json()
        
        # Return the JSON response
        return json_response

    def remove_special_characters(self, text: str) -> str:
        # Remove accents
        text = unidecode(text)
        # Remove non-alphanumeric characters except spaces
        text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
        return text

    def get_track_id_by_type(self, track: str, artist: str, search_type: str) -> str:
        # Define the endpoint URL
        base_url = "https://api.spotify.com/v1/search"
        
        # Define the headers for authorization
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        # Remove special characters from the track and artist names
        track = self.remove_special_characters(track)
        artist = self.remove_special_characters(artist)

        # Define the query parameters
        params = {
            "q": f"track:{track} artist:{artist}",
            "type": search_type,
            "limit": 1
        }

        # Make the GET request to the Spotify API
        response = requests.get(base_url, headers=headers, params=params)

        # Parse the JSON response
        json_response = response.json()

        # Check if there are any items found
        items = json_response.get(search_type + 's', {}).get('items', [])
        if items:
            # Extract and return the ID from the JSON response
            return items[0]['id']

        # If no match is found, return None
        return None

    def get_track_id(self, track: str, artist: str) -> (str, str):
        # Define the types to search for
        search_types = ["track", "episode", "show", "audiobook"]

        # Iterate through the search types and look for the item
        for search_type in search_types:
            # Call the new function to get the track ID by type
            track_id = self.get_track_id_by_type(track, artist, search_type)
            if track_id:
                # Return the ID and type if found
                return track_id, search_type

        # If no match is found, return None for both ID and type
        return None, None

    def get_track_details(self, track_id: str) -> dict:
        # Define the endpoint URL for the track
        track_url = f"https://api.spotify.com/v1/tracks/{track_id}"
        
        # Define the headers for authorization
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        # Make the GET request to the Spotify API for the track
        track_response = requests.get(track_url, headers=headers)
        
        # Parse the JSON response
        track_json = track_response.json()
        
        # Extract the desired information
        album_name = track_json['album']['name']
        album_image_url = track_json['album']['images'][0]['url']  # Assuming that the first image is the one we want
        release_date = track_json['album']['release_date']
        popularity = track_json['popularity']

        # Get the artist ID
        artist_id = track_json['artists'][0]['id']  # Assuming that the first artist is the one we want

        # Define the endpoint URL for the artist
        artist_url = f"https://api.spotify.com/v1/artists/{artist_id}"
        
        # Make the GET request to the Spotify API for the artist
        artist_response = requests.get(artist_url, headers=headers)
        
        # Parse the JSON response
        artist_json = artist_response.json()
        
        # Extract the first genre if it exists
        genres = artist_json.get('genres', [])
        genre = genres[0] if genres else None  # Or replace None with '' if you prefer a blank string

        # Return the extracted information as a dictionary
        return {
            'album_name': album_name,
            'album_image_url': album_image_url,
            'release_date': release_date,
            'genre': genre,
            'popularity': popularity
        }

    def track_id_data_quality(self, file_path):
        # Read the CSV file into a DataFrame
        df = pd.read_csv(file_path)

        # Calculate the total number of rows
        total_rows = df.shape[0]

        # Calculate the number of blank values in the track_id and album_image_url columns
        blank_track_id = df['track_id'].isna().sum()
        blank_album_image_url = df['album_image_url'].isna().sum()

        # Print the data quality information
        print(f"Total Rows: {total_rows}, Blank track_id: {blank_track_id}, Blank album_image_url: {blank_album_image_url}")

        # Create a DataFrame for plotting
        plot_df = pd.DataFrame({
            'Columns': ['Total Rows', 'track_id', 'album_image_url'],
            'Values': [total_rows, blank_track_id, blank_album_image_url]
        })

        plt.figure(figsize=[15, 5])

        # Plot the bar chart showing total rows vs blank values
        plt.subplot(1, 2, 1)
        bar1 = sns.barplot(x='Columns', y='Values', data=plot_df)
        plt.title('Total Rows vs Blank Values')
        for p in bar1.patches:
            bar1.text(p.get_x() + p.get_width()/2., p.get_height(), int(p.get_height()), ha='center')

        # Plot the bar chart showing the distribution of the type column
        plt.subplot(1, 2, 2)
        bar2 = sns.countplot(x='type', data=df)
        plt.title('Distribution of Types')
        plt.xticks(rotation=45)
        for p in bar2.patches:
            bar2.text(p.get_x() + p.get_width()/2., p.get_height(), int(p.get_height()), ha='center')

        plt.show()

    def get_track_details_new(self, track_id: str, track_type: str) -> dict:
        try:
            # Define the endpoint URL based on the track type
            if track_type == 'track':
                track_url = f"https://api.spotify.com/v1/tracks/{track_id}"
            elif track_type == 'episode':
                track_url = f"https://api.spotify.com/v1/episodes/{track_id}"
            else:
                return {}  # Return an empty dictionary if the track type is not recognized

            # Define the headers for authorization
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }

            # Make the GET request to the Spotify API for the track or episode
            track_response = requests.get(track_url, headers=headers)

            # Check for successful status code
            if track_response.status_code != 200:
                return {'error': f"Error with status code {track_response.status_code}", 'response': track_response.text}

            # Parse the JSON response
            track_json = track_response.json()

            # Initialize the result dictionary
            result = {}

            # Extract the album details if it's a track
            if track_type == 'track':
                result['album_image_url'] = track_json['album']['images'][0]['url']
                result['release_date'] = track_json['album']['release_date']
                result['popularity'] = track_json['popularity']
                result['artist'] = track_json['artists'][0]['id']
                result['genre'] = track_json['album']['genres'][0]

            # Extract the show details if it's an episode
            elif track_type == 'episode':
                result['album_image_url'] = track_json['images'][0]['url']
                result['release_date'] = track_json['release_date']
                result['genre'] = 'podcast'

            return result

        except json.JSONDecodeError as e:
            # Return the error message and the response content if JSON decoding fails
            return {'error': str(e), 'response': track_response.text}

    def get_multiple_details(self, track_ids: list, track_type: str) -> list:
        # Check if the track type is valid
        if track_type not in ["track", "episode"]:
            return []

        # Define the endpoint URL based on the track type
        base_url = f"https://api.spotify.com/v1/{track_type}s"

        # Define the headers for authorization
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        # Define the query parameters
        params = {
            "ids": ",".join(track_ids)
        }

        # Make the GET request to the Spotify API for the tracks or episodes
        response = requests.get(base_url, headers=headers, params=params)

        # Check for successful status code
        if response.status_code != 200:
            return {'error': f"Error with status code {response.status_code}", 'response': response.text}

        # Parse the JSON response
        response_json = response.json()

        # Initialize the result list
        result = []

        # Iterate through the tracks or episodes and extract the details
        for item in response_json[track_type + 's']:
            try:
                details = {}
                if track_type == 'track':
                    details['id'] = item['id']
                    details['name'] = item['name']
                    details['uri'] = item['uri']
                    details['album_image_url'] = item['album']['images'][0]['url']
                    details['release_date'] = item['album']['release_date']
                    details['popularity'] = item['popularity']
                    details['artist'] = item['artists'][0]['name']
                    details['artist_id'] = item['artists'][0]['id']
                    details['album'] = item['album']['name']
                    details['album_id'] = item['album']['id']

                elif track_type == 'episode':
                    try: 
                        details['id'] = item['id']
                        details['name'] = item['name']
                        details['uri'] = item['uri']
                        details['album_image_url'] = item['images'][0]['url']
                        details['release_date'] = item['release_date']
                        details['genre'] = 'podcast'
                        details['artist'] = item['show']['name']
                        details['artist_id'] = item['show']['id']

                    except:
                        pass
                    
                result.append(details)


                
            except Exception as e:
            # print(f"Error processing item with ID {item['id']}: {e}")
                continue

        return result

    def get_multiple_artists(self, artist_ids: list) -> list:
        # Endpoint URL
        base_url = "https://api.spotify.com/v1/artists"
        
        # Headers for authorization
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        # Query parameters
        params = {
            "ids": ",".join(artist_ids)
        }

        # Make the GET request
        response = requests.get(base_url, headers=headers, params=params)

        # Check for successful status code
        if response.status_code != 200:
            return {'error': f"Error with status code {response.status_code}", 'response': response.text}

        # Parse the JSON response
        response_json = response.json()

        # Initialize the result list
        result = []

        # Iterate through the artists and extract the details
        for artist in response_json['artists']:
            details = {
                'id': artist['id'],
                'name': artist['name'],
                'artist_genres': artist['genres'][0] if artist['genres'] else None,
                'artist_image': artist['images'][0]['url'] if artist['images'] else None
            }
            result.append(details)

        return result


    def get_multiple_albums(self, album_ids: list) -> list:
        # Endpoint URL
        base_url = "https://api.spotify.com/v1/albums"
        
        # Headers for authorization
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        # Query parameters
        params = {
            "ids": ",".join(album_ids)
        }

        # Make the GET request
        response = requests.get(base_url, headers=headers, params=params)

        # Check for successful status code
        if response.status_code != 200:
            return {'error': f"Error with status code {response.status_code}", 'response': response.text}

        # Parse the JSON response
        response_json = response.json()

        # Initialize the result list
        result = []

        # Iterate through the albums and extract the details
        for album in response_json['albums']:
            details = {
                'id': album['id'],
                'name': album['name'],
                'uri': album['uri'],
                'genres': album['genres'][0] if album['genres'] else None,
                'label': album['label']
            }
            result.append(details)

        return result



