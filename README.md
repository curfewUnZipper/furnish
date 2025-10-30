app.py — Streamlit dashboard
sentiment_analysis.py — TextBlob sentiment (toggle-ready for HF)
scraper.py — snscrape helper to fetch tweets by product name
topic_analysis.py — simple keyword extractor
data/ — sample CSVs (sofas.csv, beds.csv, chairs.csv, tables.csv, combined.csv)
requirements.txt — Python packages to install
README.md — Run instructions and notes

## How to run

1. Create a Python virtual environment (recommended):
   ```cmd
   python -m venv venv
   source venv/bin/activate   # on Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```cmd
   pip install -r requirements.txt
   python -m nltk.downloader punkt stopwords averaged_perceptron_tagger wordnet
   ```

3. Run the Streamlit app:
   ```cmd
   streamlit run app.py
   ```

