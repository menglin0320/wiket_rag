"""
This script serves as a script to crawl data from wiktenauer
a wiki for historical european martial art.
Since the crawled data is quite small.
The crawled data are saved in json format with this schema

{
  "type": "array",
  "items": {
  "type": "object",
    "properties": {
      "title": {"type": "string"},
      "url": {"type": "string", "format": "uri"},
      "n_images": {"type": "integer", "minimum": 0},
      "text": {"type": "string"}
    },
    "required": ["title", "url", "n_images", "text"],
    "additionalProperties": false
  }
}
text are in markdown format
"""
import requests
from bs4 import BeautifulSoup
import time
import random
from urllib.parse import urljoin
import json
import re
import trafilatura
import os

WIKTENAUER_USERNAME = os.getenv("WIKTENAUER_USERNAME")
WIKTENAUER_PASSWORD = os.getenv("WIKTENAUER_PASSWORD")

BASE_API = 'https://wiktenauer.com/api.php'
BASE_SITE = 'https://wiktenauer.com'

def is_wiki_page(href):
    """helper function to check if a page is a wiki page"""
    return href.startswith('/wiki/') and ':' not in href

def login(session):
    """login to wiktenauer with provided username and password
       if you don't have one you need to request an account on 
       https://wiktenauer.com/wiki/Special:RequestAccount"""
    token_params = {
        'action': 'query',
        'meta': 'tokens',
        'type': 'login',
        'format': 'json'
    }
    token_res = session.get(BASE_API, params=token_params)
    login_token = token_res.json()['query']['tokens']['logintoken']

    login_data = {
        'action': 'login',
        'lgname': WIKTENAUER_USERNAME,
        'lgpassword': WIKTENAUER_PASSWORD,
        'lgtoken': login_token,
        'format': 'json'
    }
    login_res = session.post(BASE_API, data=login_data)
    if login_res.json()['login']['result'] != 'Success':
        raise Exception("Login failed")

def get_json_response(page, session):
    """given a page, get json response"""
    params = {
        'action': 'parse',
        'page': page,
        'format': 'json'
    }
    try:
        response = session.get(BASE_API, params=params)
        response.raise_for_status()
        json_data = response.json()
    except Exception as e:
        print(f"[Error] Skipping {page}: {e}")
        return None
    return json_data

def preprocess_with_bs4(html_content):
    """Use beautiful soup to preprocess the html to change image url to <img> token,
       and add [TABLE_START] and [TABLE_END] to table tags, and add [CODE_BLOCK_START]"""
    soup = BeautifulSoup(html_content, 'html.parser')
    # Replace <img> with <image> token
    n_images = 0
    for img in soup.find_all('img'):
        img.replace_with('<image>')
        n_images += 1

    # Clean up final plain text
    text4validate = soup.get_text(separator='\n').strip()
    return soup, text4validate, n_images

def crawl_with_BFS(session, max_pages, sleep_range):
    """crawl data from wiktenauer with breadth first search

    Args:
        session (requests.sessions.Session): connection to wiktenauer
        max_pages (int): max number of pages to crawl,
                         wiktenauer is quite small so a big number basically
                         means crawl all pages
        sleep_range (List[int]): decides how long the program sleeps after crawling each page

    Returns:
        list: list of crawled pages with schema 
        {
            "type": "array",
            "items": {
            "type": "object",
                "properties": {
                "title": {"type": "string"},
                "url": {"type": "string", "format": "uri"},
                "n_images": {"type": "integer", "minimum": 0},
                "text": {"type": "string"}
                },
                "required": ["title", "url", "n_images", "text"],
                "additionalProperties": false
            }
        }
        "text" is in markdown format
    """

    # Crawler setup
    start_page = 'Main_Page'
    visited = set()
    to_visit = [start_page]
    crawled_pages = []  # Store full page text here

    while to_visit and len(visited) < max_pages:
        page = to_visit.pop(0)
        if page in visited:
            continue
        visited.add(page)

        json_data = get_json_response(page, session)
        
        if not json_data or 'error' in json_data:
            continue
        html_content = json_data['parse']['text']['*']
        title = json_data['parse']['title']

        soup, text4validate, n_images = preprocess_with_bs4(html_content)
        
        #TODO, for softlinks to wikipedia, parse the wikipedia page also.
        if text4validate.startswith("Redirect to:") or "This page is a \nsoft redirect" in text4validate:
            continue

        markdown = trafilatura.extract(
            str(soup),
            include_formatting=True,
            output_format='markdown',
            favor_precision=True
        )
        if not markdown:
            continue
        
        # Save to list
        page_url = urljoin(BASE_SITE, f'/wiki/{page}')
        crawled_pages.append({'title': title, 'text': markdown, 'url': page_url, 'n_images': n_images})
        print(f"In total {len(crawled_pages)} pages saved,  New saved page: {title}")

        # update q to continue the bfs search
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if is_wiki_page(href):
                next_page = href.split('/wiki/')[-1]
                if next_page not in visited and next_page not in to_visit:
                    to_visit.append(next_page)

        # sleep so we don't give too much pressure to the server.
        time.sleep(random.uniform(*sleep_range))
    return crawled_pages

def crawl_wikt(output_path = 'data/wikt_data.json'):
    #define session and login to wiktenauer
    session = requests.Session()
    login(session)

    #define parameters for bfs crawl and do the bfs crawl
    sleep_range = (1, 3)
    max_pages = 10000
    crawled_pages = crawl_with_BFS(session, max_pages, sleep_range)

    #save result
    print(f"\n✅ Crawled {len(crawled_pages)} pages.")
    with open(output_path, 'w') as f:
        json.dump(crawled_pages, f, ensure_ascii=False, indent=4)