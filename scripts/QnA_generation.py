import openai
import json
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

def generate_questions_answers(text, num_questions=3):
    questions_answers = []

    for _ in range(num_questions):
        # Prompt to generate questions
        messages = [
            {"role": "system", "content": "Bạn là một trợ lý hữu ích."},
            {"role": "user", "content": f"Dựa trên đoạn văn bản sau đây, hãy tạo một câu hỏi liên quan:\n\n{text}\n\nCâu hỏi:"}
        ]
        question_response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # or "gpt-3.5-turbo"
            messages=messages,
            max_tokens=50,
            temperature=0.2
        )
        question = question_response.choices[0].message['content'].strip()

        # Prompt to generate anwsers
        messages = [
            {"role": "system", "content": "Bạn là một trợ lý hữu ích."},
            {"role": "user", "content": f"Dựa trên đoạn văn bản sau đây, hãy trả lời câu hỏi sau:\n\n{text}\n\nCâu hỏi: {question}\n\nCâu trả lời:"}
        ]
        answer_response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # or "gpt-3.5-turbo"
            messages=messages,
            max_tokens=300,
            temperature=0.2
        )
        answer = answer_response.choices[0].message['content'].strip()

        questions_answers.append({"Question": question, "Answer": answer})

    return questions_answers

if __name__ == "__main__":

    folder_path = '/Users/gumiho/Gumiho/project/crawl-house-price/auto_crawler/vnexpress_text_content'

    qa_pairs = {}

    # Loop through all files in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            file_path = os.path.join(folder_path, filename)
            
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            
            qa_pairs[filename] = generate_questions_answers(text)

    output_json_path = 'output/questions_answers.json'  
    os.makedirs('output', exist_ok=True)
    # Save the generated question-answer pairs to a JSON file
    with open(output_json_path, 'w', encoding='utf-8') as json_file:
        json.dump(qa_pairs, json_file, ensure_ascii=False, indent=4)
