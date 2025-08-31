import streamlit as st
import tweepy
import praw
from googleapiclient.discovery import build
import requests
import os

# --- Helper to check for secrets file ---
def check_secrets_file():
    if not os.path.exists(".streamlit/secrets.toml"):
        print("🛑 ERROR: The '.streamlit/secrets.toml' file was not found.")
        print("Please create it with your API credentials before running this test.")
        return False
    return True

# --- Test Function for Twitter ---
def test_twitter():
    print("\n--- 🧪 Testing Twitter API ---")
    try:
        client = tweepy.Client(
            bearer_token=st.secrets["twitter"]["bearer_token"],
            consumer_key=st.secrets["twitter"]["api_key"],
            consumer_secret=st.secrets["twitter"]["api_secret"],
            access_token=st.secrets["twitter"]["access_token"],
            access_token_secret=st.secrets["twitter"]["access_secret"],
            wait_on_rate_limit=True
        )
        # A simple request to check if the client is authenticated
        response = client.search_recent_tweets("india", max_results=10)
        if response.data:
            print("✅ Twitter API Success: Successfully fetched", len(response.data), "tweets.")
        else:
            print("⚠️ Twitter API Warning: Authentication seemed to work, but no tweets were found for 'india'.")

    except Exception as e:
        print(f"❌ Twitter API Error: {e}")

# --- Test Function for Reddit ---
def test_reddit():
    print("\n--- 🧪 Testing Reddit API ---")
    try:
        client = praw.Reddit(
            client_id=st.secrets["reddit"]["client_id"],
            client_secret=st.secrets["reddit"]["client_secret"],
            user_agent=st.secrets["reddit"]["user_agent"]
        )
        # Check if the connection is read-only and valid
        print(f"Read-Only Mode: {client.read_only}")
        # Fetch one hot post from a popular subreddit
        subreddit = client.subreddit("worldnews").hot(limit=1)
        post_title = next(subreddit).title
        print(f"✅ Reddit API Success: Fetched post '{post_title}'")

    except Exception as e:
        print(f"❌ Reddit API Error: {e}")

# --- Test Function for YouTube ---
def test_youtube():
    print("\n--- 🧪 Testing YouTube API ---")
    try:
        client = build('youtube', 'v3', developerKey=st.secrets["youtube"]["api_key"])
        request = client.search().list(q="india", part="snippet", maxResults=1, type="video")
        response = request.execute()
        if response.get("items"):
            video_title = response["items"][0]["snippet"]["title"]
            print(f"✅ YouTube API Success: Fetched video '{video_title}'")
        else:
            print("⚠️ YouTube API Warning: Authentication worked, but no videos found.")
    except Exception as e:
        print(f"❌ YouTube API Error: {e}")

# --- Test Function for Google News RSS ---
def test_google_news():
    print("\n--- 🧪 Testing Google News RSS ---")
    try:
        url = "https://news.google.com/rss/search?q=india&hl=en-IN&gl=IN&ceid=IN:en"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print("✅ Google News RSS Success: Successfully connected and received data (Status Code 200).")
        else:
            print(f"❌ Google News RSS Error: Failed to connect (Status Code {response.status_code}).")
    except Exception as e:
        print(f"❌ Google News RSS Error: {e}")


if __name__ == "__main__":
    if check_secrets_file():
        test_twitter()
        test_reddit()
        test_youtube()
        test_google_news()
        print("\n--- ✅ All tests complete ---")