

import streamlit as st
import pandas as pd
import networkx as nx
from graphviz import Digraph
import plotly.express as px
import re

# Import our custom modules
from collector import get_tweets_df, get_reddit_posts_df, get_youtube_videos_df
from analysis import calculate_bot_score, build_network_graph, analyze_narrative_sentiment
from web_scraper import get_news_articles_df

# --- Page Configuration ---
st.set_page_config(page_title="Project Sentry", layout="wide", initial_sidebar_state="expanded")

# --- App Title ---
st.title("🇮🇳 Project Sentry: Anti-India Campaign Detector")
st.markdown("A system to detect and analyze coordinated anti-India campaigns across **Twitter, Reddit, YouTube, and News Media**.")

# --- Sidebar Controls ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/en/thumb/4/41/Flag_of_India.svg/1200px-Flag_of_India.svg.png", width=50)
st.sidebar.header("Mission Controls")

platform = st.sidebar.selectbox(
    "Select a Platform:",
    ("News Articles", "Reddit", "YouTube", "Twitter")
)

default_keywords = "boycott india, fascist india, kashmir under siege, hindutva terror, endia, shame on india, free kashmir"
keyword_input = st.sidebar.text_area("Keyword Database (comma-separated):", default_keywords, height=150)

if platform == "Twitter":
    max_results = st.sidebar.slider("Number of Tweets to Analyze", 50, 500, 100)
elif platform == "Reddit":
    subreddit = st.sidebar.text_input("Subreddit to Scan (or 'all')", "all")
    max_results = st.sidebar.slider("Number of Posts to Analyze", 25, 200, 50)
elif platform == "YouTube":
    max_results = st.sidebar.slider("Number of Videos to Analyze", 10, 50, 25)
else: # News Articles
    max_results = st.sidebar.slider("Number of Articles to Analyze", 10, 50, 25)

run_button = st.sidebar.button("🛡️ Run Detection")
st.sidebar.markdown("---")
st.sidebar.info("This tool analyzes live data based on the keywords provided.")
st.sidebar.markdown("---")

# --- Main Application Logic ---
if run_button:
    if not keyword_input:
        st.warning("Please provide keywords in the database to start detection.")
        st.stop()
    
    keywords = [keyword.strip() for keyword in keyword_input.split(',')]
    search_query = " OR ".join(f'"{k}"' for k in keywords if k)

    with st.spinner(f"Scanning {platform} for narratives matching keywords..."):
        if platform == "Twitter":
            df = get_tweets_df(search_query, max_results=max_results)
        elif platform == "Reddit":
            df = get_reddit_posts_df(subreddit, search_query, limit=max_results)
        elif platform == "YouTube":
            df = get_youtube_videos_df(search_query, max_results=max_results)
        else: # News Articles
            df = get_news_articles_df(keywords, max_results=max_results)

        if df.empty:
            st.error(f"Detection Failed: No recent content found on {platform} for the specified keywords. This could be due to no results or a temporary issue with the data source.")
            st.stop()

        df_final = analyze_narrative_sentiment(df)
        if platform == "Twitter":
            df_final = calculate_bot_score(df_final)
    
    st.success(f"Analysis Complete! Threat assessment for narratives on **{platform}** follows.")

    # --- Display Results ---
    tab1, tab2, tab3, tab4 = st.tabs(["Threat Dashboard", "Keyword Analysis", "Influence Network", "Raw Data"])

    # --- THREAT DASHBOARD TAB ---
    with tab1:
        anti_india_percentage = (df_final['sentiment'] == 'anti-india').sum() / len(df_final) * 100
        threat_level = "LOW"
        if anti_india_percentage > 40:
            threat_level = "HIGH"
        elif anti_india_percentage > 20:
            threat_level = "MODERATE"

        st.header("Campaign Threat Assessment")
        st.metric("Overall Threat Level", f"{threat_level}", f"{anti_india_percentage:.1f}% Anti-India Narrative", delta_color="inverse")

        st.subheader("Narrative Distribution")
        sentiment_counts = df_final['sentiment'].value_counts()
        fig = px.pie(sentiment_counts, values=sentiment_counts.values, names=sentiment_counts.index, 
                     color=sentiment_counts.index,
                     color_discrete_map={'pro-india':'#28A745', 'anti-india':'#FF4B4B', 'neutral':'#1E90FF'},
                     hole=.4)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Top Drivers of Anti-India Narrative")

        # --- FIX: Dynamically select the correct sorting column and display columns ---
        sort_col = 'engagement'
        if platform == 'YouTube':
            sort_col = 'view_count'

        if sort_col not in df_final.columns:
            st.warning(f"Could not determine top drivers. Missing key column: {sort_col}")
        else:
            anti_drivers = df_final[df_final['sentiment'] == 'anti-india'].nlargest(5, sort_col)
            
            if anti_drivers.empty:
                st.info("No significant anti-India content found in the current dataset.")
            else:
                if platform == 'Twitter':
                    st.dataframe(anti_drivers[['username', 'tweet_text', 'engagement', 'bot_score']])
                elif platform == 'Reddit':
                    st.dataframe(anti_drivers[['author', 'title', 'score', 'num_comments', 'engagement']])
                elif platform == 'YouTube':
                    st.dataframe(anti_drivers[['channel_title', 'title', 'view_count', 'like_count', 'engagement']])
                elif platform == 'News Articles':
                    st.dataframe(anti_drivers[['source', 'headline', 'link']])

    # --- KEYWORD ANALYSIS TAB ---
    with tab2:
        st.header("Keyword Performance Analysis")
        st.write("This table shows which keywords appear most frequently in detected anti-India content.")
        
        text_col = 'text_content' if 'text_content' in df_final.columns else 'tweet_text'
        if text_col in df_final.columns:
            anti_content_text = ' '.join(df_final[df_final['sentiment'] == 'anti-india'][text_col].astype(str).tolist())
            keyword_hits = []
            for keyword in keywords:
                hits = len(re.findall(r'\b' + re.escape(keyword) + r'\b', anti_content_text, re.IGNORECASE))
                if hits > 0:
                    keyword_hits.append({'Keyword': keyword, 'Occurrences in Anti-India Content': hits})
            
            if not keyword_hits:
                st.info("None of the specified keywords were found in detected anti-India content.")
            else:
                keyword_df = pd.DataFrame(keyword_hits).sort_values(by='Occurrences in Anti-India Content', ascending=False)
                st.dataframe(keyword_df, use_container_width=True)
        else:
            st.warning("Could not find a text column to analyze for keyword performance.")

    # --- INFLUENCE NETWORK TAB ---
    with tab3:
        if platform == "Twitter":
            st.header("Influence & Coordination Network")
            with st.spinner("Building influence network graph..."):
                network_g = build_network_graph(df_final)
                if not network_g.nodes() or len(network_g.edges()) == 0:
                    st.warning("Could not generate a network graph. Not enough user interactions (mentions) found.")
                else:
                    dot = Digraph()
                    # Graphviz rendering logic...
                    st.graphviz_chart(dot, use_container_width=True)
        else:
            st.info("Influence Network visualization is currently available only for Twitter data.")

    # --- RAW DATA TAB ---
    with tab4:
        st.header("Complete Raw Data")
        st.dataframe(df_final)

