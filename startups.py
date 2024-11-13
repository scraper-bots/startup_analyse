import requests
import pandas as pd
import time

# Define the range of IDs to scrape
start_id = 1  # Replace with your starting ID
end_id = 1650  # Replace with your ending ID

# Base URL for the API
base_url = "https://api.rready.com/PASHAHolding/ticket/kickbox/PASHAHolding-kickbox-"

# Headers with your authorization token and other necessary headers
headers = {
    "Authorization": "Bearer eyJraWQiOiIxIiwiYWxnIjoiRWREU0EifQ.eyJpc3MiOiJraWNrYm94LWltcHJvdmUiLCJzdWIiOiJhNjE0ZWZjOC0zMmI4LTRjYjItYjgwYi1iYzRiZDAxOGVkOWQiLCJhdWQiOiJQQVNIQUhvbGRpbmciLCJjb250ZXh0cyI6WyJQQVNIQUhvbGRpbmciXSwiZXhwIjoxNzM0MDgyMjM4fQ.AyxPsK1qbAhzt5vjTe0SFhMb37tvne_-9i2s09ppBFGlLyEh1kHkohCWvhqm9bnlfOh7hEWNjHhs34dbX0gcDA",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
}

# Initialize a list to collect data
data_list = []

# Loop through the specified range
for i in range(start_id, end_id + 1):
    url = f"{base_url}{i}"
    try:
        # Send a GET request to the API endpoint
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        data = response.json()  # Parse the JSON response
        
        # Append data to the list
        data_list.append(data)
        
        # Optional: Print status for tracking progress
        print(f"Successfully retrieved data for ID {i}")
        
        # Optional: Sleep to avoid rate limiting (if applicable)
        time.sleep(0.5)

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error for ID {i}: {http_err}")
    except Exception as err:
        print(f"Error for ID {i}: {err}")

# Convert the list of data to a pandas DataFrame
df = pd.json_normalize(data_list)

# Save the DataFrame to a CSV file (optional)
df.to_csv('api_data_scraped.csv', index=False)

# Display the DataFrame (optional)
print(df)
