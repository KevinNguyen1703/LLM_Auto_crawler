import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os

def is_recent_article(article_time):
    now = datetime.now()
    article_datetime = datetime.strptime(article_time, '%Y-%m-%dT%H:%M:%S')
    return now - timedelta(hours=3) <= article_datetime <= now

# Scrape function
def scrape_latest_articles():
    url = "https://tuoitre.vn/tin-moi-nhat.htm"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    if not os.path.exists('tuoitre_articles'):
        os.makedirs('tuoitre_articles')
            
    for article in soup.find_all('div',class_= 'box-category-item'):
        time_tag = article.find('span', class_ = 'time-ago-last-news')
        article_time = time_tag.get('title')
        if article_time and is_recent_article(article_time):
            link = article.find('a', class_ = 'box-category-link-with-avatar', href=True)['href']
            if link:
                print(f"Recent Article Link: {link}")

                if not link.startswith('https'):
                    link = 'https://tuoitre.vn' + link

                # Gửi request để lấy nội dung HTML của bài viết
                article_response = requests.get(link)
                article_response.raise_for_status()
                
                # article_filename = os.path.join('tuoitre_articles', f"{article_time}.html")
                # with open(article_filename, 'w', encoding='utf-8') as file:
                #     file.write(article_response.text) 
                               
                # Phân tích HTML để lấy nội dung chính
                article_soup = BeautifulSoup(article_response.text, 'html.parser')
                
                main_content = article_soup.find('div', class_='detail__content')
                print(main_content)
                # if main_content:
                #     # Loại bỏ các phần không cần thiết như đề xuất, quảng cáo
                #     for unwanted in main_content(['aside', 'footer', 'script', 'style', 'div', 'header']):
                #         unwanted.decompose()

                #     # Trích xuất văn bản từ nội dung chính và loại bỏ thẻ HTML
                #     text_content = main_content.get_text(separator='\n', strip=True)

                #     # Lưu văn bản vào một file .txt
                text_filename = os.path.join('tuoitre_text_content', f"{article_time.replace("/","_")}.txt")
                with open(text_filename, 'w', encoding='utf-8') as file:
                    file.write(main_content)

                #     print(f"Saved text content: {link} at {article_time.strftime('%Y-%m-%d %H:%M:%S')}")


# Run the function
scrape_latest_articles()
