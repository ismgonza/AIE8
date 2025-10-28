"""Webzio News API client."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()


class Webzio:
    """Client for webz.io News API."""
    
    def __init__(self, query: str, sentiment: str = "neutral", language: str = "english"):
        """Initialize Webzio client.
        
        Args:
            query: Search query for news articles
            sentiment: Sentiment filter (positive, negative, or neutral)
            language: Language of news articles (default: english)
        """
        self.query = query
        self.sentiment = sentiment
        self.language = language
        self.token = os.getenv("WEBZIO_API_TOKEN")
        
        if not self.token:
            raise ValueError("WEBZIO_API_TOKEN environment variable not set")
    
    def get_news(self):
        """Fetch news articles from webz.io API."""
        url = "https://api.webz.io/newsApiLite"
        params = {
            "token": self.token,
            "q": f"{self.query} language:{self.language} sentiment:{self.sentiment}",
            "size": 5
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def __str__(self):
        """Return formatted news results."""
        try:
            data = self.get_news()
            
            output = []
            output.append(f"Query: {self.query}")
            output.append(f"Sentiment: {self.sentiment}")
            output.append(f"Language: {self.language}")
            output.append(f"\nTotal Results: {data.get('totalResults', 0)}")
            output.append(f"Requests Remaining: {data.get('requestsLeft', 'N/A')}\n")
            
            posts = data.get("posts", [])
            if posts:
                output.append("Top Articles:")
                for i, post in enumerate(posts[:5], 1):
                    title = post.get("title", "No title")
                    url = post.get("url", "No URL")
                    output.append(f"{i}. {title}")
                    output.append(f"   {url}")
            else:
                output.append("No articles found.")
            
            return "\n".join(output)
        except Exception as e:
            return f"Error fetching news: {str(e)}"


if __name__ == "__main__":
    # Example usage
    client = Webzio("artificial intelligence", sentiment="positive", language="english")
    print(client)

