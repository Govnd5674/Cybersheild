import pandas as pd
import networkx as nx
from datetime import datetime, timezone
import streamlit as st

def calculate_bot_score(df):
    """
    Calculates a bot score for Twitter accounts based on several heuristics.
    A higher score indicates a higher probability of being a bot.
    """
    scores = []
    required_cols = ['user_created_at', 'followers_count', 'following_count', 'is_verified']
    if not all(col in df.columns for col in required_cols):
        df['bot_score'] = 0
        return df
        
    for index, row in df.iterrows():
        score = 0
        # Recently created accounts get a higher score
        account_age_days = (datetime.now(timezone.utc) - pd.to_datetime(row['user_created_at'])).days
        if account_age_days < 60: score += 4
        
        # Accounts with a very low follower-to-following ratio get a higher score
        if row['following_count'] > 100 and row['followers_count'] > 0:
            ratio = row['followers_count'] / row['following_count']
            if ratio < 0.1: score += 3
            
        # Accounts with very few followers get a higher score
        if row['followers_count'] < 10: score += 2
        
        # Unverified accounts get a small score increase
        if not row['is_verified']: score += 1
        
        scores.append(min(score, 10)) # Cap the score at 10
    df['bot_score'] = scores
    return df

def build_network_graph(df):
    """
    Builds a network graph of Twitter users based on mentions.
    Nodes are usernames, and an edge exists if one user mentions another.
    """
    G = nx.Graph()
    if 'tweet_text' not in df.columns or 'username' not in df.columns:
        return G

    df['username_lower'] = df['username'].str.lower()
    all_usernames = set(df['username_lower'])

    # Add all users in the dataset as nodes
    for index, row in df.iterrows():
        G.add_node(row['username'], bot_score=row.get('bot_score', 0))

    # Create edges based on mentions
    for index, row in df.iterrows():
        mentioned_users = [word.strip("@,.").lower() for word in row['tweet_text'].split() if word.startswith('@')]
        for mentioned_user in mentioned_users:
            if mentioned_user in all_usernames and row['username_lower'] != mentioned_user:
                # Find the original case-sensitive username to add the edge
                original_mentioned_user_series = df[df['username_lower'] == mentioned_user]['username']
                if not original_mentioned_user_series.empty:
                    original_mentioned_user = original_mentioned_user_series.iloc[0]
                    G.add_edge(row['username'], original_mentioned_user)

    # Calculate influence (centrality) for each node
    influence_scores = nx.degree_centrality(G)
    nx.set_node_attributes(G, influence_scores, 'influence')
    return G

def analyze_narrative_sentiment(df):
    """
    Performs keyword-based sentiment analysis to classify narratives
    as pro-India, anti-India, or neutral.
    """
    pro_india_keywords = [
        'proud indian', 'jai hind', 'india shining', 'support india', 'modi government', 
        'indian army', 'made in india', 'incredible india', 'strong india', 'unified india'
    ]
    anti_india_keywords = [
        'boycott india', 'fascist india', 'kashmir under siege', 'hindutva terror', 
        'indian government failed', 'muslim genocide', 'endia', 'shame on india', 
        'free kashmir', 'dalit lives matter', 'farmer protest'
    ]
    
    # Determine the correct text column to use based on the data source
    if 'tweet_text' in df.columns:
        text_column = 'tweet_text'
    elif 'text_content' in df.columns:
        text_column = 'text_content'
    else:
        df['sentiment'] = 'unknown' # Return if no text column found
        return df

    sentiments = []
    for text in df[text_column]:
        text_lower = str(text).lower()
        
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
