import tweepy
import pandas as pd
import praw
from googleapiclient.discovery import build
from datetime import datetime
import streamlit as st
import time


# Initialize Twitter Client
try:
    twitter_client = tweepy.Client(
        bearer_token=st.secrets["twitter"]["bearer_token"],
        consumer_key=st.secrets["twitter"]["api_key"],
        consumer_secret=st.secrets["twitter"]["api_secret"],
        access_token=st.secrets["twitter"]["access_token"],
        access_token_secret=st.secrets["twitter"]["access_secret"],
        wait_on_rate_limit=True
    )
except Exception as e:
    st.error("Could not initialize Twitter client. Please check your credentials in secrets.toml.")
    twitter_client = None

# Initialize Reddit Client
try:
    reddit_client = praw.Reddit(
        client_id=st.secrets["reddit"]["client_id"],
        client_secret=st.secrets["reddit"]["client_secret"],
        user_agent=st.secrets["reddit"]["user_agent"]
    )
except Exception as e:
    st.error("Could not initialize Reddit client. Please check your credentials in secrets.toml.")
    reddit_client = None

# Initialize YouTube Client
try:
    youtube_client = build('youtube', 'v3', developerKey=st.secrets["youtube"]["api_key"])
except Exception as e:
    st.error("Could not initialize YouTube client. Please check your credentials in secrets.toml.")
    youtube_client = None

# --- TWITTER DATA FETCHER ---
def get_tweets_df(query, max_results=100):
    if not twitter_client:
        st.warning("Twitter client is not available due to initialization error.")
        return pd.DataFrame()
    try:
        response = twitter_client.search_recent_tweets(
            query=f"{query} -is:retweet lang:en",
            max_results=min(100, max_results),
            tweet_fields=['created_at', 'public_metrics', 'text'],
            user_fields=['username', 'public_metrics', 'created_at', 'verified'],
            expansions=['author_id']
        )
        # Handle case where there is no data
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
    except tweepy.errors.TooManyRequests:
        st.error("Twitter Rate Limit Exceeded. Please wait 15 minutes before trying again.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"An error occurred while fetching tweets: {str(e)}")
        return pd.DataFrame()

# --- REDDIT DATA FETCHER ---
def get_reddit_posts_df(subreddit_name, query, limit=50):
    if not reddit_client:
        st.warning("Reddit client is not available due to initialization error.")
        return pd.DataFrame()
    try:
        subreddit = reddit_client.subreddit(subreddit_name)
        # PRAW handles rate limits automatically, so we just need a generic catch
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
        st.error(f"Error fetching Reddit posts: {e}")
        return pd.DataFrame()

# --- YOUTUBE DATA FETCHER ---
def get_youtube_videos_df(query, max_results=25):
    if not youtube_client:
        st.warning("YouTube client is not available due to initialization error.")
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
        st.error(f"Error fetching YouTube videos: {e}")
        return pd.DataFrame()
