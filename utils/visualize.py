import numpy as np
import matplotlib.pyplot as plt
from matplotlib.cm import get_cmap
from matplotlib.colors import ListedColormap
import seaborn as sns
from umap import UMAP
from langchain.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config.env import env

def plot_umap(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model=env.EMBEDDING_MODEL)
    index_name = f"faiss_index/llama-3"

    new_db = FAISS.load_local(index_name, embeddings, allow_dangerous_deserialization=True)
    chunk_embeddings = new_db.index.reconstruct_n(0, new_db.index.ntotal)
 
    chunk_embeddings = np.array(chunk_embeddings)

    query_embedding = embeddings.embed_query(user_question)

    # Combine chunk embeddings and query into one array
    all_embeddings = np.vstack([chunk_embeddings, query_embedding])

    # Reduce to 2D
    umap = UMAP(n_neighbors=15, min_dist=0.1, metric='cosine', random_state=42)
    embedding_2d = umap.fit_transform(all_embeddings)

    chunk_points = embedding_2d[:-1]
    query_point = embedding_2d[-1]

    plt.figure(figsize=(12, 8), constrained_layout=True)

    # Plot chunks
    plt.scatter(chunk_points[:, 0], chunk_points[:, 1], alpha=0.6, label="Chunks")

    # Plot query
    plt.scatter(query_point[0], query_point[1], color='red', s=150, label="User Query", marker='X')

    plt.legend()
    plt.title("Semantic Chunk Embeddings + User Query")
    plt.xlabel("UMAP Dim 1")
    plt.ylabel("UMAP Dim 2")
    plt.grid(True)
    plt.savefig("umap.png")

def plot_faiss_umap(idx):
    # Load FAISS index
    embeddings = GoogleGenerativeAIEmbeddings(model=env.EMBEDDING_MODEL)
    index_path = "faiss_index/llama-3"
    db = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)

    # Extract all stored chunk vectors from FAISS index
    chunk_vectors = db.index.reconstruct_n(0, db.index.ntotal)
    chunk_vectors = np.array(chunk_vectors)

    # UMAP dimensionality reduction
    reducer = UMAP(n_neighbors=15, min_dist=0.1, metric='cosine', random_state=42)
    reduced_embeddings = reducer.fit_transform(chunk_vectors)

    # Plot the UMAP result
    plt.figure(figsize=(10, 6))
    plt.scatter(reduced_embeddings[:, 0], reduced_embeddings[:, 1], s=20, alpha=0.7)
    plt.title("UMAP Projection of FAISS Chunk Embeddings")
    plt.xlabel("UMAP Dimension 1")
    plt.ylabel("UMAP Dimension 2")
    plt.grid(True)
    plt.savefig(f"chunks_umap_{idx}.png")
    plt.show()