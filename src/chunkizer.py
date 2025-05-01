"""
This script processes markdown text into smaller chunks for easier handling and storage. 
It reads a JSON file containing markdown data, splits the text into manageable parts 
based on word limits, and outputs the processed chunks into a new JSON file.

Key functionalities:
- Splits long text into smaller parts with a maximum word limit, Adds overlapping words to text chunks for context preservation.
- Handles markdown tables by splitting rows if necessary.
- Processes markdown blocks (text, tables, code) into chunks.

The output JSON schema:
- Each chunk includes metadata such as title, URL, number of images, chunk ID, type, and text content.
"""
from markdown_it import MarkdownIt
from markdown_it.token import Token
import re
from typing import List, Dict
import json
from tqdm import tqdm

def count_words(text: str) -> int:
    """
    Counts the number of words in a given text.

    Args:
        text (str): The input text to count words from.

    Returns:
        int: The total number of words in the text.
    """
    return len(re.findall(r'\w+', text))

def split_table_rows(table_lines: List[str], max_words: int) -> List[str]:
    """
    Groups table rows into chunks where each chunk includes a header and 
    one or more data rows, with a total word count per chunk not exceeding `max_words`.

    - Always includes the header (first two lines) in each chunk.
    - If a single row's word count exceeds `max_words`, it is still included 
      on its own row with the header, possibly split using `split_long_text`.
    - Ensures at least one row is included per chunk, even if it exceeds the word limit.

    Args:
        table_lines: List of strings representing the full table lines.
                     The first two lines are considered header.
        max_words: Maximum allowed word count per group, including the header.

    Returns:
        List of strings, each string representing one chunked table block.
    """
    header = table_lines[:2]
    header_word_count = sum(count_words(line) for line in header)
    rows = table_lines[2:]
    chunks = []
    current = header[:]
    word_count = header_word_count

    for row in rows:
        row_words = count_words(row)

        if row_words + header_word_count > max_words:
            if len(current) > 2:
                chunks.append('\n'.join(current))
                current = header[:]
                word_count = header_word_count
            chunks.append('\n'.join(header + row))
            continue

        if word_count + row_words > max_words and len(current) > 2:
            chunks.append('\n'.join(current))
            current = header[:]
            word_count = header_word_count

        current.append(row)
        word_count += row_words

    if len(current) > 2:
        chunks.append('\n'.join(current))
    return chunks

def split_markdown_blocks(md_text: str, max_words: int = 200, overlap_words: int = 30) -> List[Dict]:
    """
    This code splits markdown blocks first
    Then it splits markdown text into smaller chunks based on word limits, preserving context 
    by adding overlapping words between chunks.

    Args:
        md_text (str): The markdown text to be split into chunks.
        max_words (int, optional): Maximum number of words allowed per chunk. Defaults to 200.
        overlap_words (int, optional): Number of overlapping words between consecutive chunks. Defaults to 30.

    Returns:
        List[Dict]: A list of dictionaries, where each dictionary represents a chunk with metadata 
                    such as type ('text', 'table', or 'code') and the chunk's content.
    """
    md = MarkdownIt()
    tokens = md.parse(md_text)
    
    chunks = []
    current_chunk = []
    current_word_count = 0

    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.type == "table_open": # table
            table_lines = []
            while i < len(tokens) and tokens[i].type != "table_close":
                table_lines.append(tokens[i].content)
                i += 1
            table_lines.append(tokens[i].content)  # include table_close
            table_text = '\n'.join(line for line in table_lines if line.strip())

            table_words = count_words(table_text)
            if table_words <= max_words:
                chunks.append({"type": "table", "text": table_text})
            else:
                row_lines = table_text.strip().split('\n')
                table_chunks = split_table_rows(row_lines, max_words)
                for t in table_chunks:
                    chunks.append({"type": "table", "text": t})
            import pdb
            pdb.set_trace()
        elif token.type == "fence":  # code block
            if current_chunk:
                chunks.append({
                    "type": "text",
                    "text": '\n'.join(current_chunk)
                })
                current_chunk = []
                current_word_count = 0

            code_words = token.content.strip().split()
            step = max_words - overlap_words
            for j in range(0, len(code_words), step):
                chunk_words = code_words[j:j + max_words]
                if chunk_words:
                    chunks.append({
                        "type": "code",
                        "text": ' '.join(chunk_words)
                    })
        elif token.type == "inline" or token.type.endswith("_open"): #normal text
            content = token.content.strip()
            if content:
                words = content.split()
                total_words = len(words)

                if total_words > max_words:
                    if current_chunk:
                        chunks.append({
                            "type": "text",
                            "text": '\n'.join(current_chunk)
                        })
                        current_chunk = []
                        current_word_count = 0

                    step = max_words - overlap_words
                    for j in range(0, total_words, step):
                        chunk_words = words[j:j + max_words]
                        if chunk_words:
                            chunks.append({
                                "type": "text",
                                "text": ' '.join(chunk_words)
                            })

                elif current_word_count + total_words > max_words:
                    if current_chunk:
                        chunks.append({
                            "type": "text",
                            "text": '\n'.join(current_chunk)
                        })
                    current_chunk = [content]
                    current_word_count = total_words
                else:
                    current_chunk.append(content)
                    current_word_count += total_words
        i += 1

    if current_chunk:
        chunks.append({
            "type": "text",
            "text": '\n'.join(current_chunk)
        })

    #add chunk_id to meta data
    for i, chunk in enumerate(chunks):
        chunk['chunk_id'] = i

    return chunks

def chunknize_data(data_path, out_path):
    """
    Processes a JSON file containing markdown data, splits the text into chunks, 
    and saves the processed chunks into a new JSON file.

    Args:
        data_path (str): Path to the input JSON file containing markdown data.
    """
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    # get chunks
    all_chunks = []
    for sample in tqdm(data):
        title, url, n_images = sample['title'], sample['url'], sample['n_images']
        chunks = split_markdown_blocks(sample['text'])
        chunks = [{"title": title,
                   "url": url,
                   "n_images": n_images,
                   "chunk_id": i,
                   "type": chunk['type'],
                   "text": chunk["text"]} for i, chunk in enumerate(chunks)]
        all_chunks.extend(chunks)
    with open(out_path, 'w') as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=4)