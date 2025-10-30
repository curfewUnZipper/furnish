from textblob import TextBlob
from transformers import pipeline

hf_sentiment = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")

def analyze_sentiment(text, engine="huggingface"):
    # if engine == "huggingface":
        # result = hf_sentiment(text[:512])[0]
        # return {"label": result["label"].lower(), "score": result["score"]}
        
    # else:
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.1:
        label = "positive"
    elif polarity < -0.1:
        label = "negative"
    else:
        label = "neutral"
    return {"label": label, "score": polarity}
