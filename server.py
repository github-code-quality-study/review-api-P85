import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from urllib.parse import parse_qs, urlparse
import json
import pandas as pd
from datetime import datetime
import uuid
import os
from typing import Callable, Any
from wsgiref.simple_server import make_server

nltk.download('vader_lexicon', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('stopwords', quiet=True)

adj_noun_pairs_count = {}
sia = SentimentIntensityAnalyzer()
stop_words = set(stopwords.words('english'))

reviews = pd.read_csv('data/reviews.csv').to_dict('records')
locations = [
"Albuquerque, New Mexico",
"Carlsbad, California",
"Chula Vista, California",
"Colorado Springs, Colorado",
"Denver, Colorado",
"El Cajon, California",
"El Paso, Texas",
"Escondido, California",
"Fresno, California",
"La Mesa, California",
"Las Vegas, Nevada",
"Los Angeles, California",
"Oceanside, California",
"Phoenix, Arizona",
"Sacramento, California",
"Salt Lake City, Utah",
"Salt Lake City, Utah",
"San Diego, California",
"Tucson, Arizona",
]

class ReviewAnalyzerServer:
    def __init__(self) -> None:
        # This method is a placeholder for future initialization logic
        pass

    def analyze_sentiment(self, review_body):
        sentiment_scores = sia.polarity_scores(review_body)
        return sentiment_scores

    def __call__(self, environ: dict[str, Any], start_response: Callable[..., Any]) -> bytes:
        """
        The environ parameter is a dictionary containing some useful
        HTTP request information such as: REQUEST_METHOD, CONTENT_LENGTH, QUERY_STRING,
        PATH_INFO, CONTENT_TYPE, etc.
        """
        

        if environ["REQUEST_METHOD"] == "GET":
            # Create the response body from the reviews and convert to a JSON byte string
            query_s = parse_qs(environ["QUERY_STRING"])
            # Write your code here
            new_reviews = []
            for review in reviews:
                timestamp = datetime.strptime(review["Timestamp"],"%Y-%m-%d %H:%M:%S")

                location_fil = ("location" not in query_s) or ( review["Location"] in query_s["location"])
                start_fil = ("start_date" not in query_s) or (datetime.strptime(query_s["start_date"][0], "%Y-%m-%d") <= timestamp)
                end_fil = ("end_date" not in query_s) or (datetime.strptime(query_s["end_date"][0], "%Y-%m-%d") >= timestamp)

                if location_fil and start_fil and end_fil:
                    review["sentiment"] = self.analyze_sentiment(review["ReviewBody"])
                    new_reviews.append(review)
    

            response_body = json.dumps(new_reviews, indent=2).encode("utf-8")

            # Set the appropriate response headers
            start_response("200 OK", [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(response_body)))
             ])
            
            return [response_body]


        if environ["REQUEST_METHOD"] == "POST":
            try:
                request_body_size = int(environ.get('CONTENT_LENGTH', 0))
            except (ValueError):
                request_body_size = 0

            request_body = environ['wsgi.input'].read(request_body_size).decode("utf-8")

            data = parse_qs(request_body)
            if 'Location' not in data or 'ReviewBody' not in data:
                 start_response("400 FAILED", [
                   ("Content-Type", "application/json"),
             ])
                 return []
            
            location = data.get('Location',[''])[0] 
            review = data.get('ReviewBody',[''])[0] 
            
            if location not in locations:
                 start_response("400 FAILED", [
                   ("Content-Type", "application/json"),
             ])
                 return []


            # query_s =environ["PATH_INFO"]
            res = {"ReviewId": str(uuid.uuid4()), 
                    "ReviewBody": review, 
                    "Location": location, 
                    "Timestamp":str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))}
            # Write your code here

            response_body =json.dumps(res,indent=2).encode("utf-8")
            # Set the appropriate response headers
            start_response("201 OK", [
            ("Content-Type", "application/json"),
               ("Content-Length", str(len(response_body)))
        
             ])
            
            return [response_body]

if __name__ == "__main__":
    app = ReviewAnalyzerServer()
    port = os.environ.get('PORT', 8000)
    with make_server("", port, app) as httpd:
        print(f"Listening on port {port}...")
        httpd.serve_forever()