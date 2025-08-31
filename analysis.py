import pandas as pd
import networkx as nx
from datetime import datetime, timezone
import streamlit as st

# This function is from your latest version
def calculate_bot_score(df):
    scores = []
    # Check if necessary columns exist, otherwise return df with a default score
    if 'user_created_at' not in df.columns or 'followers_count' not in df.columns or 'following_count' not in df.columns or 'is_verified' not in df.columns:
        df['bot_score'] = 0
        return df
        
    for index, row in df.iterrows():
        score = 0
        account_age_days = (datetime.now(timezone.utc) - pd.to_datetime(row['user_created_at'])).days
        if account_age_days < 60: score += 4
        if row['following_count'] > 100 and row['followers_count'] > 0: # Avoid division by zero
            ratio = row['followers_count'] / row['following_count']
            if ratio < 0.1: score += 3
        if row['followers_count'] < 10: score += 2
        if not row['is_verified']: score += 1
        scores.append(min(score, 10))
    df['bot_score'] = scores
    return df

# This function is from your latest version
def build_network_graph(df):
    G = nx.Graph()
    if 'tweet_text' not in df.columns:
        return G

    df['username_lower'] = df['username'].str.lower()
    all_usernames = set(df['username_lower'])

    for index, row in df.iterrows():
        G.add_node(row['username'], bot_score=row.get('bot_score', 0))

    for index, row in df.iterrows():
        mentioned_users = [word.strip("@,.").lower() for word in row['tweet_text'].split() if word.startswith('@')]
        for mentioned_user in mentioned_users:
            if mentioned_user in all_usernames and row['username_lower'] != mentioned_user:
                original_mentioned_user_series = df[df['username_lower'] == mentioned_user]['username']
                if not original_mentioned_user_series.empty:
                    original_mentioned_user = original_mentioned_user_series.iloc[0]
                    G.add_edge(row['username'], original_mentioned_user)

    influence_scores = nx.degree_centrality(G)
    nx.set_node_attributes(G, influence_scores, 'influence')
    return G

# --- MODIFIED FOR PROBLEM STATEMENT ---
def analyze_narrative_sentiment(df):
    """
    Performs keyword-based sentiment analysis to classify narratives
    as pro-India, anti-India, or neutral.
    """
    # Expanded keyword lists for better accuracy
    pro_india_keywords = [
        'proud indian', 'jai hind', 'india shining', 'support india', 'modi government', 
        'indian army', 'made in india', 'incredible india', 'strong india', 'unified india'
    ]
    anti_india_keywords = [
        'boycott india', 'fascist india', 'kashmir under siege', 'hindutva terror', 
        'indian government failed', 'muslim genocide', 'endia', 'shame on india', 
        'free kashmir', 'dalit lives matter', 'farmer protest'
    ]
    
    # Determine the correct text column to use
    if 'tweet_text' in df.columns:
        text_column = 'tweet_text'
    elif 'text_content' in df.columns:
        text_column = 'text_content'
    else:
        df['sentiment'] = 'unknown'
        return df

    sentiments = []
    for text in df[text_column]:
        text_lower = str(text).lower()
        
        # Score based on keyword presence
        pro_score = sum(1 for word in pro_india_keywords if word in text_lower)
        anti_score = sum(1 for word in anti_india_keywords if word in text_lower)
        
        if anti_score > pro_score:
            sentiments.append('anti-india')
        elif pro_score > anti_score:
            sentiments.append('pro-india')
        else:
            sentiments.append('neutral')
            
    df['sentiment'] = sentiments
    return df

