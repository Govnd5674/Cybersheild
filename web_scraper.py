import pandas as pd
import requests
from bs4 import BeautifulSoup

def get_news_articles_df(keywords, max_results=50):
    """
    Fetches news articles from the Google News RSS feed by combining all
    keywords into a single, efficient query.
    
    Args:
        keywords (list): A list of search terms.
        max_results (int): The maximum number of articles to return in total.
        
    Returns:
        pandas.DataFrame: DataFrame containing news article data.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    all_records = []
    seen_links = set()

    if not keywords:
        return pd.DataFrame()
        
    search_query = " OR ".join(f'"{k.strip()}"' for k in keywords if k.strip())
    
    try:
        url_query = requests.utils.quote(search_query)
        url = f"https://news.google.com/rss/search?q={url_query}&hl=en-IN&gl=IN&ceid=IN:en"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        items = soup.find_all('item', limit=max_results)
        
        for item in items:
            link = item.link.text if item.link else ""
            if link in seen_links:
                continue
            
            seen_links.add(link)
            title = item.title.text if item.title else "No Title"
            source = item.source.text if item.source else "No Source"
            
            all_records.append({
                'headline': title,
                'source': source,
                'link': link,
                'text_content': title,
                'engagement': 0
            })

    except requests.exceptions.RequestException as e:
        print(f"Could not fetch news for query '{search_query}': {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"An error occurred while parsing news: {e}")
        return pd.DataFrame()

    if not all_records:
        return pd.DataFrame()
        
    return pd.DataFrame(all_records)
