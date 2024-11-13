import requests
import json
import pandas as pd

# Load the previously scraped data from the provided file
file_path = 'api_data_scraped.csv'
scraped_data_df = pd.read_csv(file_path)

# Extract unique creator IDs from the DataFrame
unique_creator_ids = scraped_data_df['creator'].unique()

# Define the API endpoint for fetching creator information
url = "https://api.rready.com/PASHAHolding/users/fetchByBatch"

# Headers for the POST request (including your token)
headers = {
    "Authorization": "Bearer eyJraWQiOiIxIiwiYWxnIjoiRWREU0EifQ.eyJpc3MiOiJraWNrYm94LWltcHJvdmUiLCJzdWIiOiJhNjE0ZWZjOC0zMmI4LTRjYjItYjgwYi1iYzRiZDAxOGVkOWQiLCJhdWQiOiJQQVNIQUhvbGRpbmciLCJjb250ZXh0cyI6WyJQQVNIQUhvbGRpbmciXSwiZXhwIjoxNzM0MDgyMjM4fQ.AyxPsK1qbAhzt5vjTe0SFhMb37tvne_-9i2s09ppBFGlLyEh1kHkohCWvhqm9bnlfOh7hEWNjHhs34dbX0gcDA",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Convert the list of unique creator IDs to a JSON payload
payload = {
    "targets": unique_creator_ids.tolist()  # Corrected key name based on provided example
}

# Make the POST request to fetch creator details
response = requests.post(url, headers=headers, data=json.dumps(payload))

# Check if the request was successful
if response.status_code == 200:
    creator_data = response.json()  # Parse the JSON response
    # Convert the data to a DataFrame for easy viewing and processing
    creator_df = pd.json_normalize(creator_data)
    
    # Display the DataFrame (optional)
    print(creator_df)
    
    # Save the data to a CSV file (optional)
    creator_df.to_csv('creator_data.csv', index=False)
else:
    print(f"Failed to fetch data: {response.status_code} - {response.text}")
