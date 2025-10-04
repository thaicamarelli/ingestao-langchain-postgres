# Ingestao do PDF no PGVector
import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFDirectoryLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_postgres import PGVector

load_dotenv()

for variable in ("OPENAI_API_KEY", "PGVECTOR_URL", "PGVECTOR_COLLECTION"):
    if not os.getenv(variable):
        raise RuntimeError(f"Environment variable {variable} is not set")

embeddings = OpenAIEmbeddings(model=os.getenv("OPENAI_MODEL","text-embedding-3-small"))

def load_document():
    current_dir = Path(__file__).parent
    pdf_path = current_dir.parent / "document.pdf"
    docs = PyPDFLoader(str(pdf_path)).load()
    print(f"Carregando documento de: {pdf_path}")
    print(f"Tipo dos documentos: {type(docs)}")
    return docs

def split_document(docs):
    splits = RecursiveCharacterTextSplitter(chunk_size=100,chunk_overlap=50, add_start_index=False).split_documents(docs)
    
    if not splits:
        raise SystemExit(0)

    enriched = [
        Document(
            page_content=d.page_content,
            metadata={k: v for k, v in d.metadata.items() if v not in ("", None)}
        )
        for d in splits
    ]

    ids = [f"doc-{i}" for i in range(len(enriched))]

    print(type(enriched), type(ids))
    return enriched, ids

def save_doc_vectors_in_db(enriched_data, doc_ids):
    store = PGVector(
        embeddings=embeddings,
        collection_name=os.getenv("PGVECTOR_COLLECTION"),
        connection=os.getenv("PGVECTOR_URL"),
        use_jsonb=True,
    )

    store.add_documents(documents=enriched_data, ids=doc_ids)

def main():
    load_document()


main()



