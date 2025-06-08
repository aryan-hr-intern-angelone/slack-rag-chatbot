import os
from PyPDF2 import PdfReader
import fitz
import pymupdf4llm
from langchain.schema import Document
from langchain.vectorstores.utils import DistanceStrategy
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_cohere import CohereEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from config.env import env

doc_metadata = {}

def get_pdf_text(pdf_stream):
    try:
        stream = fitz.open(stream=pdf_stream, filetype="pdf")
        md_text = pymupdf4llm.to_markdown(stream)
        return md_text
    except Exception as e:    
        print(e)

# def get_pdf_text(pdf_stream):
#     text = ""
#     # print("reading pdf stream")
#     # pdf_reader = PdfReader(pdf_stream)
#     # for page in pdf_reader.pages:
#     #     extracted = page.extract_text()
#     #     if extracted:
#     #         text += extracted
#     try:
#         stream = fitz.open(stream=pdf_stream, filetype="pdf")
#         md_text = pymupdf4llm.to_markdown(stream)
#         return md_text
#     except Exception as e:
#         print(e)
#     # return text
    
def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1024,
        chunk_overlap=128,
        separators=["\n\n", "\n", ".", " "]
    )
    # text_splitter = RecursiveCharacterTextSplitter(
    #     chunk_size=configs["chunk_size"],
    #     chunk_overlap=configs["chunk_overlap"],
    #     separators=["\n\n", "\n", ".", " "]
    # )
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(chunks, model_name, file_id, file_name):
    try:
        index_path = "faiss_index"
        os.makedirs(index_path, exist_ok=True)
        index_file = os.path.join(index_path, model_name)

        # embeddings = CohereEmbeddings(model=env.EMBEDDING_MODEL)
        embeddings = GoogleGenerativeAIEmbeddings(model=env.EMBEDDING_MODEL)
        documents = [Document(page_content=chunk, metadata={"source": file_name}) for chunk in chunks]

        new_store=FAISS.from_documents(
            documents,
            embeddings,
            distance_strategy=DistanceStrategy.COSINE
        )

        meta_dict = new_store.docstore._dict
        for key, val in meta_dict.items():
            if file_id not in doc_metadata:
                doc_metadata[file_id] = [key]
            else:
                doc_metadata[file_id].append(key)

        if os.path.exists(index_file):
            existing_store = FAISS.load_local(index_file, embeddings, allow_dangerous_deserialization=True)
            existing_store.merge_from(new_store)
            existing_store.save_local(index_file)
        else:
            print("index file not found")
            new_store.save_local(index_file)
    except Exception as e:
        print(e)

def delete_index(model_name, file_id):
    file_path = os.path.join("faiss_index", model_name)
    # embeddings = CohereEmbeddings(model=env.EMBEDDING_MODEL)
    embeddings = GoogleGenerativeAIEmbeddings(model=env.EMBEDDING_MODEL)

    if os.path.exists(file_path):
        existing_store = FAISS.load_local(file_path, embeddings, allow_dangerous_deserialization=True)
        for key in doc_metadata[file_id]:
            existing_store.docstore.delete(key)
        existing_store.save_local(file_path)
        print(f"Deleted {file_id} from vector store")
        doc_metadata[file_id] = []
    else:
        print(f"Index file not found for {file_id}")
