from src.wikt_crawler import crawl_wikt
from src.chunkizer import chunknize_data

if __name__ == '__main__':
    raw_wikt_markdown_path = 'data/wikt_data.json'
    chunknized_data_path = 'data/wikt_chunks.json'
    crawl_wikt(raw_wikt_markdown_path)
    chunknize_data(raw_wikt_markdown_path, chunknized_data_path)
