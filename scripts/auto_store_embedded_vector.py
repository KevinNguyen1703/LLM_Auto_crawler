from pinecone import Pinecone, ServerlessSpec
import os
import openai
from dotenv import load_dotenv
import argparse

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

def init_pinecone_client():
    pinecone = Pinecone(api_key=os.getenv('PINECONE_API_KEY'), environment=os.getenv('ENVIRONMENT_REGION'))
    # Create index (only need to do this once)
    index_name = os.getenv('PINECONE_INDEX_NAME')
    if index_name not in pinecone.list_indexes():
        pinecone.create_index(
            name=index_name, 
            dimension=1536,
            metric='euclidean',
            spec=ServerlessSpec(
                cloud='aws',
                region=os.getenv('ENVIRONMENT_REGION')
            ))  
    # Connect to the index
    index = pinecone.Index(index_name)
    
    return index
    
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
        response = openai.Embedding.create(
            input=item['text'],
            model=embedded_model
        )
        embedding = response['data'][0]['embedding']
        embeddings.append({"id": item['id'], "vector": embedding})
    return embeddings

# Function to store embeddings in Pinecone
def store_embeddings(folder_path):
    index = init_pinecone_client()
    text_data = read_txt_file(folder_path=folder_path)
    embeddings = generate_embeddings(texts=text_data)
    for embedding in embeddings:
        index.upsert([(embedding['id'], embedding['vector'])])

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Script to auto store embedding vector into cloud vectordb")
    parser.add_argument('--folder', type=str, default="/Users/gumiho/Gumiho/project/crawl-house-price/auto_crawler/vnexpress_text_content")  # Required argument

    args = parser.parse_args()
    
    store_embeddings(args.folder)
    