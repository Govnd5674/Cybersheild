import streamlit as st
import pandas as pd
import networkx as nx
from graphviz import Digraph
import plotly.express as px
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt

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
    ("News Articles", "Reddit", "YouTube","Twitter")
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
    # --- ADDED TIMESTAMP ---
    st.info(f"Data last fetched at: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")


    # --- Display Results ---
    tab1, tab2, tab3, tab4 = st.tabs(["Threat Dashboard", "Keyword Analysis", "Influence Network", "Raw Data"])

    # --- THREAT DASHBOARD TAB ---
    with tab1:
        st.header("Campaign Threat Assessment")
        
        # --- Create a 2x2 grid for visualizations ---
        row1_col1, row1_col2 = st.columns(2)
        row2_col1, row2_col2 = st.columns(2)
        
        with row1_col1:
            st.subheader("Narrative Distribution")
            sentiment_counts = df_final['sentiment'].value_counts()
            fig_pie = px.pie(sentiment_counts, values=sentiment_counts.values, names=sentiment_counts.index, 
                         color=sentiment_counts.index,
                         color_discrete_map={'pro-india':'#28A745', 'anti-india':'#FF4B4B', 'neutral':'#1E90FF'},
                         hole=.4)
            st.plotly_chart(fig_pie, use_container_width=True)

        with row1_col2:
            st.subheader("Top Anti-India Sources")
            anti_india_df = df_final[df_final['sentiment'] == 'anti-india']
            source_col_map = {
                'Twitter': 'username', 'Reddit': 'author', 
                'YouTube': 'channel_title', 'News Articles': 'source'
            }
            source_col = source_col_map.get(platform)
            
            if not anti_india_df.empty and source_col and source_col in anti_india_df.columns:
                top_sources = anti_india_df[source_col].value_counts().nlargest(5)
                fig_bar = px.bar(top_sources, x=top_sources.values, y=top_sources.index, orientation='h', 
                                 labels={'y': 'Source', 'x': 'Number of Posts'}, color_discrete_sequence=['#FF4B4B'])
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No significant anti-India sources found.")

        with row2_col1:
            st.subheader("Activity Over Time")
            date_col_map = {
                'Twitter': 'tweet_created_at', 'Reddit': 'created_at', 'YouTube': 'published_at'
            }
            date_col = date_col_map.get(platform)
            
            if date_col and date_col in df_final.columns:
                # FIX: Use errors='coerce' to handle unparseable dates gracefully
                df_final['parsed_date'] = pd.to_datetime(df_final[date_col], errors='coerce')
                
                # Drop rows where the date could not be parsed
                time_df = df_final.dropna(subset=['parsed_date'])
                
                if not time_df.empty:
                    post_counts = time_df.set_index('parsed_date').resample('D').size().reset_index(name='count')
                    fig_line = px.line(post_counts, x='parsed_date', y='count', title="Posts per Day", labels={'parsed_date': 'Date'})
                    st.plotly_chart(fig_line, use_container_width=True)
                else:
                    st.info("Could not parse dates for time series analysis.")
            else:
                st.info("Time series analysis not available for News Articles.")

        with row2_col2:
            if platform == "Twitter":
                st.subheader("Bot Score Distribution")
                if 'bot_score' in df_final.columns:
                    fig_hist = px.histogram(df_final, x='bot_score', nbins=10, 
                                            title="Distribution of Bot Scores",
                                            color_discrete_sequence=['#FF4B4B'])
                    st.plotly_chart(fig_hist, use_container_width=True)
                else:
                    st.info("Bot score analysis not available.")
            else:
                st.info("Bot score analysis is only available for Twitter.")

        st.subheader("Top Drivers of Anti-India Narrative (by Engagement)")
        sort_col = 'engagement'
        if platform == 'YouTube': sort_col = 'view_count'

        if sort_col not in df_final.columns:
            st.warning(f"Could not determine top drivers. Missing key column: {sort_col}")
        else:
            anti_drivers = df_final[df_final['sentiment'] == 'anti-india'].nlargest(5, sort_col)
            
            if anti_drivers.empty:
                st.info("No significant anti-India content found in the current dataset.")
            else:
                display_cols_map = {
                    'Twitter': ['username', 'tweet_text', 'engagement', 'bot_score'],
                    'Reddit': ['author', 'title', 'score', 'num_comments', 'engagement'],
                    'YouTube': ['channel_title', 'title', 'view_count', 'like_count', 'engagement'],
                    'News Articles': ['source', 'headline', 'link']
                }
                st.dataframe(anti_drivers[display_cols_map[platform]])

    # --- KEYWORD ANALYSIS TAB ---
    with tab2:
        st.header("Keyword & Narrative Analysis")
        
        text_col = 'text_content' if 'text_content' in df_final.columns else 'tweet_text'
        if text_col in df_final.columns:
            anti_content_text = ' '.join(df_final[df_final['sentiment'] == 'anti-india'][text_col].astype(str).tolist())
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Keyword Performance")
                keyword_hits = []
                for keyword in keywords:
                    hits = len(re.findall(r'\b' + re.escape(keyword) + r'\b', anti_content_text, re.IGNORECASE))
                    if hits > 0:
                        keyword_hits.append({'Keyword': keyword, 'Occurrences': hits})
                
                if not keyword_hits:
                    st.info("None of the specified keywords were found in detected anti-India content.")
                else:
                    keyword_df = pd.DataFrame(keyword_hits).sort_values(by='Occurrences', ascending=False)
                    st.dataframe(keyword_df, use_container_width=True)

            with col2:
                st.subheader("Word Cloud from Anti-India Content")
                if anti_content_text.strip():
                    wordcloud = WordCloud(width=800, height=400, background_color='white', colormap='Reds').generate(anti_content_text)
                    fig_wc, ax = plt.subplots()
                    ax.imshow(wordcloud, interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig_wc)
                else:
                    st.info("Not enough text to generate a word cloud.")
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
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.subheader("Network Graph")
                        dot = Digraph(comment='Influence Network')
                        dot.attr(rankdir='LR', size='12,8', splines='true', overlap='false')
                        dot.attr('node', shape='circle', style='filled')

                        for node, attrs in network_g.nodes(data=True):
                            bot_score = attrs.get('bot_score', 0)
                            color = '#FF4B4B' if bot_score > 5 else '#1E90FF'
                            dot.node(node, label=node, color=color, fontcolor='white')

                        for u, v in network_g.edges():
                            dot.edge(u, v)

                        st.graphviz_chart(dot, use_container_width=True)

                    with col2:
                        st.subheader("Top Influencers")
                        node_data = []
                        for node, attrs in network_g.nodes(data=True):
                            node_data.append({
                                'Username': node,
                                'Influence': attrs.get('influence', 0),
                                'Bot Score': attrs.get('bot_score', 0),
                                'Connections': network_g.degree(node)
                            })
                        
                        influencers_df = pd.DataFrame(node_data).sort_values(by='Influence', ascending=False).reset_index(drop=True)
                        st.dataframe(influencers_df, use_container_width=True)
        else:
            st.info("Influence Network visualization is currently available only for Twitter data.")

    # --- RAW DATA TAB ---
    with tab4:
        st.header("Complete Raw Data")
        st.dataframe(df_final)

