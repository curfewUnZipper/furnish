import tweepy
import pandas as pd

def scrape_tweets_for_product(product_name, limit=100):
    bearer_token = "AAAAAAAAAAAAAAAAAAAAAE9x5AEAAAAABQxfvt%2FBnjNa%2FISyrUI0e6OzScg%3DBClUbEeeUYidr1uBsQaIOuH4dDXWfB30zYtzOqfN5qFb3fZKkJ"  # <--- try hardcoding here temporarily
    client = tweepy.Client(bearer_token=bearer_token)
    query = f'"{product_name}" lang:en -is:retweet'
    tweets = client.search_recent_tweets(query=query, max_results=min(limit, 100), tweet_fields=["created_at", "lang", "text"])
    
    data = []
    if tweets.data:
        for t in tweets.data:
            data.append({
                "text": t.text,
                "date": t.created_at,
                "region": "unknown",
                "product_name": product_name
            })
    return pd.DataFrame(data)
