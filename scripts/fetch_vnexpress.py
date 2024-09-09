import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os

def fetch_recent_articles():
    url = 'https://vnexpress.net/tin-tuc-24h'
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    # Tạo thư mục để lưu các file văn bản
    if not os.path.exists('vnexpress_text_content'):
        os.makedirs('vnexpress_text_content')

    # Lấy giờ hiện tại
    now = datetime.now()
    
    # Tìm các bài viết có thời gian đăng trong vòng 3 giờ trở lại
    articles = soup.find_all('article', class_='item-news')
    for article in articles:
        time_element = article.find('span', class_='time-ago')
        if time_element and time_element.has_attr('datetime'):
            # Lấy thời gian từ thuộc tính datetime
            article_time = datetime.fromisoformat(time_element['datetime'])

            # Kiểm tra nếu bài viết được đăng trong vòng 3 giờ trở lại
            if article_time >= now - timedelta(hours=3):
                link = article.find('a', href=True)['href']
                if not link.startswith('https'):
                    link = 'https://vnexpress.net' + link

                # Gửi request để lấy nội dung HTML của bài viết
                article_response = requests.get(link)
                article_response.raise_for_status()
                
                # Phân tích HTML để lấy nội dung chính
                article_soup = BeautifulSoup(article_response.text, 'html.parser')
                
                # Giả sử nội dung chính nằm trong thẻ <article> hoặc <div class="main-content">
                main_content = article_soup.find('article')
                if not main_content:
                    main_content = article_soup.find('div', class_='main-content')

                if main_content:
                    # Loại bỏ các phần không cần thiết như đề xuất, quảng cáo
                    for unwanted in main_content(['aside', 'footer', 'script', 'style', 'div', 'header']):
                        unwanted.decompose()

                    # Trích xuất văn bản từ nội dung chính và loại bỏ thẻ HTML
                    text_content = main_content.get_text(separator='\n', strip=True)

                    # Lưu văn bản vào một file .txt
                    text_filename = os.path.join('vnexpress_text_content', f"{article_time.strftime('%Y%m%d_%H%M%S')}.txt")
                    with open(text_filename, 'w', encoding='utf-8') as file:
                        file.write(text_content)

                    print(f"Saved text content: {link} at {article_time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    fetch_recent_articles()
