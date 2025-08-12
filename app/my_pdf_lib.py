import re
from io import BytesIO
from typing import Any, Dict, List
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from pypdf import PdfReader
from ollama_connector import ollama_embeddings
import os
from pathlib import Path

# where to  import user/password asnd so on? to connect ot the ur?

# Define the absolute path to the indexes directory
APP_ROOT = Path(__file__).resolve().parent
INDEX_BASE = Path(os.getenv("FAISS_INDEX_DIR", APP_ROOT / "indexes"))


def parse_pdf(file: BytesIO) -> List[str]:
    pdf = PdfReader(file)
    output = []
    for page in pdf.pages:
        text = page.extract_text()
        # Merge hyphenated words
        text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
        # Fix newlines in the middle of sentences
        text = re.sub(r"(?<!\n\s)\n(?!\s\n)", " ", text.strip())
        # Remove multiple newlines
        text = re.sub(r"\n\s*\n", "\n\n", text)
        output.append(text)
    return output


def text_to_docs(text: str, filename: str) -> List[Document]:
    """Converts a string or list of strings to a list of Documents
    with metadata."""
    if isinstance(text, str):
        # Take a single string as one page
        text = [text]
    page_docs = [Document(page_content=page) for page in text]

    # Add page numbers as metadata
    for i, doc in enumerate(page_docs):
        doc.metadata["page"] = i + 1

    # Split pages into chunks
    doc_chunks = []

    for doc in page_docs:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
            chunk_overlap=100,
        )
        chunks = text_splitter.split_text(doc.page_content)
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk, metadata={"page": doc.metadata["page"], "chunk": i, "filename": filename}
            )
            # Add sources a metadata
            doc.metadata["source"] = f"{doc.metadata['page']}-{doc.metadata['chunk']}"
            doc_chunks.append(doc)
    return doc_chunks


def get_index_for_pdf(pdf_files):
    documents = []
    for pdf_file in pdf_files:
        pdf_text = parse_pdf(BytesIO(pdf_file.getvalue()))  # Extract text from the pdf
        filename = pdf_file.name  # Get the filename
        documents = documents + text_to_docs(pdf_text, filename)  # Divide the text up into chunks

    index = FAISS.from_documents(documents, ollama_embeddings)
    return index


def store_index_in_db(index, name):
    index_dir = INDEX_BASE / name
    # Create the directory if it doesn't exist
    index_dir.mkdir(parents=True, exist_ok=True)
    index.save_local(str(index_dir))

def load_index_from_db(index_name):
    index_dir = INDEX_BASE / index_name
    faiss_path = index_dir / "index.faiss"
    pkl_path   = index_dir / "index.pkl"

    if not faiss_path.exists() or not pkl_path.exists():
        raise FileNotFoundError(f"FAISS index missing: {faiss_path} or {pkl_path}")

    index = FAISS.load_local(str(index_dir), ollama_embeddings, allow_dangerous_deserialization=True)
    return index
