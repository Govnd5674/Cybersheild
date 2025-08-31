import tweepy
import pandas as pd
import praw
from googleapiclient.discovery import build
from datetime import datetime

# --- CREDENTIALS (FROM YOUR INPUT) ---
# Twitter API Credentials
TWITTER_API_KEY = "9cmmEfuTupk9QKlhvkWUWU7xe"
TWITTER_API_SECRET = "ZhvlR11UUaLekGgwZ0qplulX4o2jb9Tj4Hs2sUBMfDUP6xKwtl"
TWITTER_ACCESS_TOKEN = "1368203703732248579-lAKxRvwtW4WPW8Tc9dxy9Vqus5pn9t"
TWITTER_ACCESS_SECRET = "JKs6nv7UcFnu4qXvJjNZgxeHWLlgKxAaDQh70DX5EqPE5"
TWITTER_BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAALsQ3wEAAAAAUXph5Lp9IgndkKCJ1Qe%2FM3psotE%3DM9R9LKS5hKCck2K4lPbuWNlJc5zmgUPt5s13k4HgO8cOEIu0xx"

# Reddit API Credentials
REDDIT_CLIENT_ID = "qmSrf7HH5NlGuJ1DSiVxEg"
REDDIT_CLIENT_SECRET = "fQm-DAEqTUFZ7KasmoP90xtaQgC04w"
REDDIT_USER_AGENT = "myredditapp by u/govindchudari"

# YouTube API Credentials
YOUTUBE_API_KEY = "AIzaSyCa_SH2jtrhcRxZnOdmG2gYIs3EkK38b00"

# --- CLIENT INITIALIZATION ---
try:
    twitter_client = tweepy.Client(
        consumer_key=TWITTER_API_KEY,
        consumer_secret=TWITTER_API_SECRET,
        access_token=TWITTER_ACCESS_TOKEN,
        access_token_secret=TWITTER_ACCESS_SECRET,
        bearer_token=TWITTER_BEARER_TOKEN,
        wait_on_rate_limit=True
    )
except Exception as e:
    twitter_client = None

try:
    reddit_client = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )
except Exception as e:
    reddit_client = None

try:
    youtube_client = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
except Exception as e:
    youtube_client = None

# --- TWITTER DATA FETCHER ---
def get_tweets_df(query, max_results=100):
    if not twitter_client:
        print("Twitter client not initialized.")
        return pd.DataFrame()
    try:
        response = twitter_client.search_recent_tweets(
            query=f"{query} -is:retweet lang:en",
            max_results=min(100, max_results),
            tweet_fields=['created_at', 'public_metrics', 'text'],
            user_fields=['username', 'public_metrics', 'created_at', 'verified'],
            expansions=['author_id']
        )
        if not response.data: return pd.DataFrame()

        users = {user.id: user for user in response.includes['users']}
        records = []
        for tweet in response.data:
            user = users[tweet.author_id]
            records.append({
                'author_id': tweet.author_id, 'username': user.username,
                'user_created_at': user.created_at, 'followers_count': user.public_metrics['followers_count'],
                'following_count': user.public_metrics['following_count'], 'tweet_count': user.public_metrics['tweet_count'],
                'is_verified': user.verified, 'tweet_text': tweet.text,
                'tweet_created_at': tweet.created_at, 'retweet_count': tweet.public_metrics['retweet_count'],
                'like_count': tweet.public_metrics['like_count']
            })
        
        df = pd.DataFrame(records)
        df['engagement'] = df['retweet_count'] + df['like_count']
        return df.sort_values('engagement', ascending=False)
    except Exception as e:
        print(f"An error occurred while fetching tweets: {str(e)}")
        return pd.DataFrame()

# --- REDDIT DATA FETCHER ---
def get_reddit_posts_df(subreddit_name, query, limit=50):
    if not reddit_client:
        print("Reddit client not initialized.")
        return pd.DataFrame()
    try:
        subreddit = reddit_client.subreddit(subreddit_name)
        records = [{
            'title': post.title, 'author': post.author.name if post.author else '[deleted]',
            'score': post.score, 'num_comments': post.num_comments, 'url': post.url,
            'created_at': datetime.utcfromtimestamp(post.created_utc),
            'text_content': post.title + " " + post.selftext
        } for post in subreddit.search(query, limit=limit, sort='new')]
            
        if not records: return pd.DataFrame()
        df = pd.DataFrame(records)
        df['engagement'] = df['score'] + df['num_comments']
        return df.sort_values('engagement', ascending=False)
    except Exception as e:
        print(f"Error fetching Reddit posts: {e}")
        return pd.DataFrame()

# --- YOUTUBE DATA FETCHER ---
def get_youtube_videos_df(query, max_results=25):
    if not youtube_client:
        print("YouTube client not initialized.")
        return pd.DataFrame()
    try:
        search_response = youtube_client.search().list(q=query, part='snippet', maxResults=max_results, type='video').execute()
        video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
        if not video_ids: return pd.DataFrame()

        video_response = youtube_client.videos().list(part='snippet,statistics', id=','.join(video_ids)).execute()
        records = []
        for video in video_response.get('items', []):
            stats = video.get('statistics', {})
            records.append({
                'title': video['snippet']['title'], 'channel_title': video['snippet']['channelTitle'],
                'published_at': video['snippet']['publishedAt'], 'view_count': int(stats.get('viewCount', 0)),
                'like_count': int(stats.get('likeCount', 0)), 'comment_count': int(stats.get('commentCount', 0)),
                'video_url': f"https://www.youtube.com/watch?v={video['id']}",
                'description': video['snippet']['description']
            })

        df = pd.DataFrame(records)
        df['engagement'] = df['view_count'] + df['like_count'] + df['comment_count']
        df['text_content'] = df['title'] + " " + df['description']
        return df.sort_values('engagement', ascending=False)
    except Exception as e:
        print(f"Error fetching YouTube videos: {e}")
        return pd.DataFrame()

# --- END OF SCRIPT ---
# Developed by Govind Choudhary for Project Sentry
# This script is part of a system to detect and analyze anti-India campaigns.

