# wiket_rag

`wiket_rag` is a specialized Retrieval-Augmented Generation (RAG) system designed for Wiktenauer, a comprehensive online resource for historical European martial arts (HEMA). This tool processes markdown data from Wiktenauer, chunks it into manageable pieces, and enables users to ask questions about the content using a conversational interface powered by a language model.

## Features

- **Wiktenauer Data Crawling**: Crawl Wiktenauer data and convert it to markdown.
- **Markdown Data Processing**: Parses and chunks markdown content from Wiktenauer, including text, tables, and code blocks.
- **Vector Database**: Stores processed chunks in a vector database for efficient similarity-based retrieval.
- **Conversational Interface**: Provides a Streamlit-based chat interface for querying Wiktenauer content.
- **Customizable LLM**: Uses OpenAI's GPT-based models for answering questions, with support for fine-tuning parameters like temperature.

## Installation

To set up the project, clone the repository and install the required dependencies:

```bash
git clone https://github.com/yourusername/wiket_rag.git
cd wiket_rag
pip install -r requirements.txt
```

## Usage

After installation, follow these steps to use `wiket_rag`:

### Get the Chunks

#### Option 1: Use a Wiktenauer Account

1. **Set Up Environment Variables**:
   Export your Wiktenauer credentials as environment variables:
   ```bash
   export WIKTENAUER_USERNAME=your_username
   export WIKTENAUER_PASSWORD=your_password
   ```

2. **Run the Preprocessing Step**:
   Use the `create_vdb_chunks.py` script to fetch data and generate chunks:
   ```bash
   python create_vdb_chunks.py
   ```

#### Option 2: Download Preprocessed Data

If you do not have a Wiktenauer account, you can download preprocessed data or chunks from the provided Google Drive links:
- [Download Wiktenauer Data](https://drive.google.com/file/d/1pBbooamrSsXoKRgBqGt3xSY5AD4I8LfY/view?usp=sharing)
- [Download Wiktenauer Chunks](#) ([replace with actual link](https://drive.google.com/file/d/1ODCfdZlWpOa9MunJaLJJ_JTca_4S3wMb/view?usp=sharing))
Then put them to the data folder.

### Run the Chat Interface

Before starting the chat interface, ensure you have set up your OpenAI account credentials as environment variables:
```bash
export OPENAI_API_KEY=your_openai_api_key
```

Once the data chunks are available in the `data` folder (from either option), you can start the chat interface using the `wikt_chat.py` script:
```bash
streamlit run wikt_chat.py
```

This will allow you to interact with the Wiktenauer content through a conversational interface.

