import requests
from bs4 import BeautifulSoup
# The new, unified SDK structure:
from google import genai
from google.genai import types # Contains the corrected class name (GenerateContentConfig)
import os
import json 
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from .env file (if using locally)
load_dotenv()

# --- Gemini Configuration Functions (Best Practice for Structured Output) ---

def get_response_schema() -> Dict[str, Any]:
    """Defines the strict JSON schema for the model's output."""
    article_schema = {
        "type": "OBJECT",
        "properties": {
            "headline": {"type": "STRING", "description": "The main headline of the news article."},
            "summary": {"type": "STRING", "description": "A brief summary of the article (2-3 sentences)."},
            "key_points": {
                "type": "ARRAY",
                "description": "A list of the 2-4 most critical takeaways.",
                "items": {"type": "STRING"}
            }
        },
        "required": ["headline", "summary", "key_points"],
        "propertyOrdering": ["headline", "summary", "key_points"]
    }

    # The root object contains fixed categories
    categories = ["World", "Business", "Technology", "Entertainment", "Sports", "Science", "Health"]
    root_properties = {
        category: {
            "type": "ARRAY",
            "description": f"List of articles belonging to the {category} category.",
            "items": article_schema
        }
        for category in categories
    }

    return {
        "type": "OBJECT",
        "properties": root_properties,
        "required": categories
    }


# --- Scraper Class ---

headers = {
 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

class Website:

    def __init__(self, url):
        """
        Create this Website object from the given url using the BeautifulSoup library
        """
        self.url = url
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status() # Raise exception for bad status codes
            soup = BeautifulSoup(response.content, 'html.parser')
            self.title = soup.title.string if soup.title else "No title found"
            
            # Filter irrelevant elements
            if soup.body:
                for irrelevant in soup.body(["script", "style", "img", "input", "nav", "footer", "header", "form"]):
                    irrelevant.decompose()
                
                # Extract clean text
                self.text = soup.body.get_text(separator="\n", strip=True)
            else:
                self.text = "No body content found"
        
        except requests.exceptions.RequestException as e:
            self.title = "Scraping Error"
            self.text = f"Failed to retrieve website content: {e}"


# --- News Extractor Class ---

class NewsExtractor:
    def __init__(self):
        # Use the new Client initialization pattern for the unified SDK (google-genai)
        
        api_key = os.getenv("GEMINI_API_KEY")
        
        if api_key:
            # Initialize the client with the API key
            self.client = genai.Client(api_key=api_key)
        else:
            # Initialize the client without a key if it's expected to be injected by the environment
            self.client = genai.Client()
            print("Warning: GEMINI_API_KEY not found. Using default client initialization.")

        self.model_name = 'gemini-2.5-flash'
    
    def extract_news(self, website_text: str):
        
        # 1. Define the System Instructions (Embedded in the prompt)
        prompt_instructions = """
        You are a news content extractor. Your response **MUST** be a single, raw JSON object (no wrappers, no prose) 
        that strictly adheres to the provided JSON schema.
        
        From the following website content, please:
        
        1. Identify and extract the main news articles.
        2. Classify each article into one of the following categories: "World", "Business", "Technology", "Entertainment", "Sports", "Science", "Health".
        3. For each article, provide: Headline, Brief summary (2-3 sentences), and Key points (a list of critical takeaways).
        4. Filter out advertisements, navigation menus, and all irrelevant, non-news content.
        5. prioritize articles up, as per their importance, scale and effect from Indian prespective.
        6. Skip an artical if you feel that the same news has alrady accured.
        
        If a category has no content, its array should be empty ([]).
        
        Website Content:
        """
        
        # 2. Construct the full prompt (Instructions + User Content)
        full_prompt = prompt_instructions + website_text
        
        # 3. Define the Generation Config for Structured JSON Output
        # This class name is correct in the new 'google-genai' SDK
        config = types.GenerateContentConfig( 
            response_mime_type="application/json",
            response_schema=get_response_schema()
        )
        
        print("Sending request to Gemini API to extract structured news...")
        
        try:
            # Call generate_content using the client object
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[full_prompt],
                config=config
            )
            
            # The JSON output is usually stored in response.text when using structured output
            try:
                # Attempt to parse the resulting JSON string
                parsed_json = json.loads(response.text)
                return parsed_json
            except json.JSONDecodeError:
                return f"Error: Model returned invalid JSON. Raw text: {response.text}"
            
        except Exception as e:
            # Catch API errors (e.g., rate limiting, bad authentication)
            return f"Error communicating with Gemini API: {str(e)}"

# usage

    def feed(self, url, url1, url2):
        try:
            
            te0 = Website(url)
            te1 = Website(url1)
            te2 = Website(url2)

            

            # print(f"Website Title: {te.title}")
            # print("-" * 50)
            
            if "Failed to retrieve" in te0.text:
                print(te0.text)
            elif "Failed to retrieve" in te1.text:
                print(te1.text)
            elif "Failed to retrieve" in te2.text:
                print(te2.text)
            else:
                # Limiting the content size for the API call to avoid exceeding token limits for large news sites
                MAX_CONTENT_LENGTH = 55000 
                combined_text = f"{te0.text}\n\n--- NEXT WEBSITE ---\n\n{te1.text}\n\n--- NEXT WEBSITE ---\n\n{te2.text}"
                mk = combined_text[:MAX_CONTENT_LENGTH]
                if len(combined_text) > MAX_CONTENT_LENGTH:
                    print(f"NOTE: Truncating scraped content to {MAX_CONTENT_LENGTH} characters for API call.")

                # Extract news using Gemini
                news_extractor = NewsExtractor()  # Uses environment variable or default client
                news_content = news_extractor.extract_news(mk)
                
                if isinstance(news_content, dict):
                    # Pretty print the final JSON
                    state = "\n--- SUCCESSFULLY EXTRACTED NEWS (JSON) ---"
                    #print(json.dumps(news_content, indent=4))
                    #print("------------------------------------------")
                    # with open("news.json", "w") as f:
                    #     json.dump(news_content, f, indent=4)
                    return state,  news_content
                    
                elif isinstance(news_content, str):
                    state = "--- EXTRACTION FAILED (SEE ERROR) ---"
                    print(f"Error details: {news_content}")
                    # Uncomment below lines if you want to see scraped content for debugging
                    # print("\nRAW SCRAPED CONTENT (first 1000 chars for debugging):")
                    # print("-" * 50)
                    # print(mk[:1000] + "..." if len(mk) > 1000 else mk)
                    return state, news_content

        except ValueError as e:
            print(f"Initialization Error: {e}")
            print("\nTo use Gemini API, please ensure the 'GEMINI_API_KEY' environment variable is set.")
        except Exception as e:
            print(f"An unexpected error occurred during execution: {e}")
