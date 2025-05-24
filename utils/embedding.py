import os
from PyPDF2 import PdfReader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

load_dotenv()

doc_metadata = {}

def get_pdf_text(pdf_stream):
    text = ""
    pdf_reader = PdfReader(pdf_stream)
    for page in pdf_reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted
    return text

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=300)
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(chunks, model_name, file_id):
    try:
        index_path = "faiss_index"
        os.makedirs(index_path, exist_ok=True)
        index_file = os.path.join(index_path, model_name)

        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        new_store=FAISS.from_texts(chunks, embeddings)

        meta_dict = new_store.docstore._dict
        for key, val in meta_dict.items():
            if file_id not in doc_metadata:
                doc_metadata[file_id] = [key]
            else:
                doc_metadata[file_id].append(key)

        print(doc_metadata)

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
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    if os.path.exists(file_path):
        existing_store = FAISS.load_local(file_path, embeddings, allow_dangerous_deserialization=True)
        for key in doc_metadata[file_id]:
            existing_store.docstore.delete(key)
        existing_store.save_local(file_path)
        print(f"Deleted {file_id} from vector store")
        doc_metadata[file_id] = []
    else:
        print(f"Index file not found for {file_id}")
