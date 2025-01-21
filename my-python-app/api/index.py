import requests
import re
import time
import os
from flask import Flask, jsonify, request

app = Flask(__name__)

# Function to clear the console
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

# Function to extract access token from cookies
def get_access_token_from_cookie(cookie):
    r = requests.Session()
    r.headers.update({
        'Accept-Language': 'id,en;q=0.9',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        'Referer': 'https://www.instagram.com/',
        'Host': 'www.facebook.com',
        'Sec-Fetch-Mode': 'cors',
        'Accept': '*/*',
        'Connection': 'keep-alive',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-Dest': 'empty',
        'Origin': 'https://www.instagram.com',
        'Accept-Encoding': 'gzip, deflate'
    })

    try:
        response = r.get('https://www.facebook.com/x/oauth/status?client_id=124024574287414&wants_cookie_data=true&origin=1&input_token=&sdk=joey&redirect_uri=https://www.instagram.com/brutalid_/', cookies={'cookie': cookie})
        if '"access_token":' in str(response.headers):
            token = re.search('"access_token":"(.*?)"', str(response.headers)).group(1)
            return token
        else:
            return None
    except Exception as e:
        print(f"Error occurred while extracting token: {str(e)}")
        return None

# Function to get group IDs from a file
def get_group_ids_from_file(filename):
    group_ids = []
    try:
        with open(filename, 'r') as file:
            group_links = file.readlines()
            for link in group_links:
                match = re.search(r'facebook\.com/groups/(\d+)', link.strip())
                if match:
                    group_ids.append(match.group(1))
    except FileNotFoundError:
        print(f"{filename} not found.")
        exit()
    return group_ids

# Function to share a post using the access token (user token)
def share_post(user_token, group_id, post_link):
    post_url = f"https://graph.facebook.com/v18.0/{group_id}/feed"
    data = {
        'link': post_link,
        'access_token': user_token
    }

    response = requests.post(post_url, data=data)

    if response.status_code == 200:
        print(f"Post shared successfully in group ID {group_id}.")
        return True
    else:
        print(f"Post can't be shared in group ID {group_id}. Error: {response.status_code}, {response.text}")
        return False

# Function to get tokens from cookies file
def get_tokens_from_file(filename):
    tokens = []
    try:
        with open(filename, 'r') as file:
            cookies = file.readlines()
            for cookie in cookies:
                token = get_access_token_from_cookie(cookie.strip())
                if token:
                    tokens.append(token)
                time.sleep(2)
    except FileNotFoundError:
        print(f"{filename} not found.")
        exit()
    return tokens

# Function to share the post in batches using next cookie after 4 groups
def share_in_batches(tokens, group_ids, post_link):
    num_groups = len(group_ids)
    group_count = 0  # To keep track of how many groups we've shared to
    batch_size = 4  # Share in batches of 4 groups per token

    # Process each token and share the post in 4 groups at a time
    while group_count < num_groups and tokens:  # Check if there are still tokens available
        token = tokens.pop(0)  # Use the first token in the list
        print(f"\nUsing Token: {token}")

        # Share 4 groups with this cookie
        for i in range(group_count, min(group_count + batch_size, num_groups)):
            group_id = group_ids[i]
            success = share_post(token, group_id, post_link)
            if success:
                print(f"Post shared to group with ID: {group_id}")
            else:
                print(f"Failed to share in group with ID: {group_id}")
            time.sleep(2)  # Small delay between requests

        group_count += batch_size  # After every batch of 4 groups, move to the next batch

    if not tokens:
        print("\nAll cookies have been used. Process is complete.")
    else:
        print("\nSome groups are remaining. But no cookies left.")

# Flask route to trigger the sharing process
@app.route('/share', methods=['POST'])
def share():
    data = request.get_json()

    cookie_file = data['cookie_file']
    groups_file = data['groups_file']
    post_link = data['post_link']

    # Step 1: Get tokens from cookies file
    tokens = get_tokens_from_file(cookie_file)

    if not tokens:
        return jsonify({"error": "No valid tokens found."}), 400

    # Step 2: Get group IDs from the file
    group_ids = get_group_ids_from_file(groups_file)
    if not group_ids:
        return jsonify({"error": "No valid group IDs found."}), 400

    # Step 3: Share the post in batches
    share_in_batches(tokens, group_ids, post_link)
    return jsonify({"message": "Post sharing process initiated successfully."})

if __name__ == '__main__':
    app.run(debug=True)
