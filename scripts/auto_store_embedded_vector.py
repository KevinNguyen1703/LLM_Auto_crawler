from pinecone import Pinecone, ServerlessSpec
import os
import openai
from openai import AzureOpenAI
from dotenv import load_dotenv
import argparse
from pymilvus import Milvus, FieldSchema, Collection, CollectionSchema, DataType, connections

load_dotenv()
# openai.api_key = os.getenv('OPENAI_API_KEY')
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-04-01-preview",
)
MAX_CONTENT_LENGTH=4096
def init_pinecone_client():
    pinecone = Pinecone(api_key=os.getenv('PINECONE_API_KEY'), environment=os.getenv('ENVIRONMENT_REGION'))
    # Create index (only need to do this once)
    index_name = os.getenv('PINECONE_INDEX_NAME')
    if not any(index["name"] == index_name for index in pinecone.list_indexes()):
        pinecone.create_index(
            name=index_name, 
            dimension=4096,
            metric='euclidean',
            spec=ServerlessSpec(
                cloud='aws',
                region=os.getenv('ENVIRONMENT_REGION')
            ))  
    # Connect to the index
    index = pinecone.Index(index_name)
    
    return index

def init_milvus_client():
    milvus_client = Milvus(host=os.getenv('MILVUS_HOST'), port=os.getenv('MILVUS_PORT'))
    # Define schema for the collection
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=255, is_primary=True),  # Use VARCHAR or INT64
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=1536),
        FieldSchema(name="plain_text", dtype=DataType.VARCHAR, max_length=MAX_CONTENT_LENGTH)
    ]
    collection_schema = CollectionSchema(fields)
    collection_name = os.getenv('MILVUS_COLLECTION_NAME')

    if not milvus_client.has_collection(collection_name):
        milvus_client.create_collection(collection_name, collection_schema)
        
    return milvus_client, collection_name
    
def read_txt_file(folder_path):
    # Read text files from the folder
    text_data = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                text_data.append({"id": filename, "text": content})
    return text_data

# Function to generate embeddings
def generate_embeddings(texts, embedded_model="text-embedding-ada-002"):
    embeddings = []
    for item in texts:
        response = client.embeddings.create(
            model="text3small",
            input=item['text']
        )
        embedding = list(response.data[0])[0][1]
        embeddings.append({"id": item['id'], "vector": embedding})
    return embeddings

# Function to store embeddings in Pinecone
def store_embeddings(folder_path, vector_db):
    text_data = read_txt_file(folder_path=folder_path)
    embeddings = generate_embeddings(texts=text_data)
    if vector_db == 'pinecone':
        index = init_pinecone_client()
        for embedding in embeddings:
            index.upsert([(embedding['id'], embedding['vector'])])
    elif vector_db == 'milvus':
        milvus_client, collection_name = init_milvus_client()
        connections.connect("default", host=os.getenv('MILVUS_HOST'), port=os.getenv('MILVUS_PORT'))
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=255, is_primary=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),
            FieldSchema(name="plain_text", dtype=DataType.VARCHAR, max_length=1024)
        ]
        # schema = CollectionSchema(fields, collection_name)
        collection = Collection(name=collection_name)
        ids, emds = [], []
        for embedding in embeddings:
            ids.append(embedding['id'])
            emds.append(embedding['vector']) 
        texts = []
        for item in text_data:
            text = item['text']
            words = text.split()
            truncated_words = words[:MAX_CONTENT_LENGTH//2]
            truncated_content = " ".join(truncated_words)
            texts.append(truncated_content)
            
        data = [ids,emds,texts]
        collection.insert(data)
        collection.flush()


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Script to auto store embedding vector into cloud vectordb")
    parser.add_argument('--folder', type=str, default="/Users/gumiho/Gumiho/project/crawl-house-price/auto_crawler/vnexpress_text_content")  # Required argument
    parser.add_argument('--db', type=str, choices=['pinecone', 'milvus'], default='pinecone')
    
    args = parser.parse_args()
    
    store_embeddings(args.folder, vector_db=args.db)
    