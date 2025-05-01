from llama_index.core.prompts.base import PromptTemplate

condense_question_prompt = PromptTemplate(
    """Given the following conversation and a new user message, rewrite the new message into a standalone question suitable for retrieving from the historical european martial art Wiki.

<Chat History>
{chat_history}

<New User Message>
{question}

Standalone question:
"""
)

response_prompt = PromptTemplate(
    """You are a helpful assistant answering questions about historical European martial arts (HEMA) using only the provided context.

Instructions:
- For each claim you make, include a short excerpt or quote from the source to justify it.
- At the end, include a “References” section listing each source's full URL. No repeat.

Context:
{context_str}

Question:
{query_str}

Answer:
"""
)