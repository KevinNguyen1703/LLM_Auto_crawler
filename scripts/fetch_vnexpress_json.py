import requests
import re
import json
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os

def crawl_vnexpress_news(soup, url):
    info_dict = {}
    # Extract URL
    info_dict['url'] = url
    # Extract date
    date_span = soup.find('span', class_='date')
    info_dict['date'] = date_span.get_text(strip=True) if date_span else "Date not found"
    # Extract category
    breadcrumb_ul = soup.find('ul', class_='breadcrumb')
    first_li = breadcrumb_ul.find('li') if breadcrumb_ul else None
    info_dict['category'] = first_li.get_text(strip=True) if first_li else "Category not found"
    # Extract title
    title_h1 = soup.find('h1')
    if title_h1:
        info_dict['title'] = title_h1.get_text(strip=True) or soup.find('title').get_text(strip=True)
    else:
        info_dict['title'] = "Title not found"
    # Extract description
    description_p = soup.find('p', class_='description')
    info_dict['description'] = description_p.get_text(strip=False) if description_p else "Description not found"
    # Remove figures, images, and unwanted elements
    article = soup.find('article', class_='fck_detail')
    if article:
        for tag in article.find_all(['figure', 'img', 'script', 'style', 'div']):
            tag.decompose()  # Remove these tags completely
        # Extract and clean content
        paragraphs = article.find_all('p', class_='Normal')
        content = "\n\n".join([p.get_text(strip=False) for p in paragraphs])
        # Clean URLs and strange characters
        content = re.sub(r'http\S+|www\S+', '', content)  # Remove URLs
        content = re.sub(r'[^\w\s,.!?$%&*#@()-]', '', content)  # Keeps common symbols and removes undefined characters
        content = content.strip()
        info_dict['content'] = content
    else:
        info_dict['content'] = "Content not found"
    return info_dict

def save_html(soup, output_dir, file_name=''):
    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    # Create a new BeautifulSoup object for the cleaned content
    clean_soup = BeautifulSoup('<html><head></head><body></body></html>', 'html.parser')
    # Extract and add meta tags to the head section
    meta_tags = soup.find_all('meta')
    for meta_tag in meta_tags:
        clean_soup.head.append(meta_tag)
    # Extract relevant sections
    title_h1 = soup.find('h1')
    date_span = soup.find('span', class_='date')
    category = soup.find('ul', class_='breadcrumb').find('li') if soup.find('ul', class_='breadcrumb') else None
    description_p = soup.find('p', class_='description')
    article = soup.find('article', class_='fck_detail')
    # Add the title if it exists
    if title_h1:
        clean_soup.head.append(title_h1)
    # Add the date if it exists
    if date_span:
        clean_soup.body.append(date_span)
    # Add the category if it exists
    if category:
        clean_soup.body.append(category)
    # Add the description if it exists
    if description_p:
        clean_soup.body.append(description_p)
    # Process the article content to remove unnecessary tags
    if article:
        # Remove unnecessary tags like figures, images, scripts, styles, and divs
        for tag in article.find_all(['figure', 'img', 'script', 'style', 'div']):
            tag.decompose()  # Remove these tags completely
        # Add the cleaned article content directly to the body
        clean_soup.body.append(article)
    # Define the full file path
    file_path = os.path.join(output_dir, file_name)
    # Write the cleaned HTML content to the file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(clean_soup.prettify())


def fetch_vnexpress_articles():
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
                text_filename = os.path.join('vnexpress_text_content', f"{article_time.strftime('%Y%m%d_%H%M%S')}.json")
                save_html(article_soup, 'vnexpress_text_content', f"{article_time.strftime('%Y%m%d_%H%M%S')}.html")
                data = crawl_vnexpress_news(article_soup, link)
                with open(text_filename, 'w', encoding='utf-8') as file:
                    json.dump(data, file, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    fetch_vnexpress_articles()