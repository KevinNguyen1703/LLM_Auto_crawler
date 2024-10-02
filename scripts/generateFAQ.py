import os
import openai
import json
from dotenv import load_dotenv
from openai import AzureOpenAI
import argparse

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-04-01-preview",
)
def generate_single_qa_pair(content):
    messages = [
    {"role": "system", "content": """
     Bạn là một trợ lý hữu ích hỗ trợ tôi tạo ra các cặp câu hỏi và câu trả lời. Tôi sẽ gửi nội dung một bài báo và bạn cần tạo ra chỉ một cặp câu hỏi-câu trả lời có dạng sau.
     Q: ...
     A: ..."""},
    {"role": "user", "content": f"Hãy tạo một cặp câu hỏi câu trả lời tiêu biểu nhất dựa trên nội dung bài báo sau: \n\n{content}\n\n"}
    ]
    
    response = client.chat.completions.create(
        model="gpt4omini",
        messages=messages,
        max_tokens=150, 
        n=1,
        stop=None,
        temperature=0.7
    )
    
    return response.choices[0].message.content

def parse_single_qa_pair(qa_text):
    lines = qa_text.split('\n')
    if len(lines) >= 2:
        question = lines[0].strip().replace("Q: ", "").replace("Q1:", "")
        answer = lines[1].strip().replace("A: ", "").replace("A1:", "")
        return {"question": question, "answer": answer}
    return None

def process_json_files_in_folder(folder_path):
    result_list = []
    
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)

        if os.path.isfile(file_path) and file_name.endswith('.json'):
            print(f"Processing {file_name}")
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                
                content = json_data.get("content", "")
                if content:
                    try:
                        qa_text = generate_single_qa_pair(content)
                    except Exception as e:
                        print(f"Cannot generate qa pair due to: {e}")
                        continue
                    
                    try:
                        qa_pair = parse_single_qa_pair(qa_text)
                    except Exception as e:
                        print(f"Cannot parse qa pair due to: {e}")
                        continue
                                  
                    if qa_pair:
                        json_data["question"] = qa_pair["question"]
                        json_data["answer"] = qa_pair["answer"]
                        print(f"question: {qa_pair["question"]}")
                        print(f"answer: {qa_pair["answer"]}")
                        result_list.append(json_data)
                    else:
                        print(f"Skipping {file_name}: No QA pair generated.")
                else:
                    print(f"Skipping {file_name}: Content field is empty.")
    
    return result_list

def process_text_files_in_folder(folder_path):
    qa_list = []
    
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        print(f"Processing {file_name}")
        if os.path.isfile(file_path) and os.path.getsize(file_path) >=1024:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                try:
                    qa_text = generate_single_qa_pair(content)  # Generate a single QA pair
                except Exception as e:
                    print(f"Cannot generate qa pair due to: {e}")
                    continue
                print(qa_text)
                try:
                    parsed_qa = parse_single_qa_pair(qa_text)  # Parse the QA pair
                except Exception as e:
                    print(f"Cannot parse qa pair due to: {e}")
                    continue
                if parsed_qa:
                    qa_list.append({
                        "page": file_name,
                        "question": parsed_qa["question"],
                        "answer": parsed_qa["answer"]
                    })
        else:
            print(f"Skipping {file_name} (size less than 1KB or not a file)")
    
    return qa_list

def save_to_json(qa_list, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(qa_list, f, ensure_ascii=False, indent=4)

# folder_path = '/Users/gumiho/Gumiho/project/crawl-house-price/auto_crawler/vnexpress_text_content'  
# qa_list = process_text_files_in_folder(folder_path)
# save_to_json(qa_list, 'qa_pairs.json')  

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate question-answer pairs from text files.")
    parser.add_argument('input_folder', type=str, help="Path to the folder containing the text files.")
    parser.add_argument('output_file', type=str, help="Path to the output JSON file.")

    args = parser.parse_args()

    # Process files in the input folder and save the results to the output JSON file
    json_result_list = process_json_files_in_folder(args.input_folder)
    save_to_json(json_result_list, args.output_file)
