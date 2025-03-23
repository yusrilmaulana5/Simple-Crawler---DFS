import requests
from bs4 import BeautifulSoup
import mysql.connector
from urllib.parse import urljoin
from flask import Flask, render_template_string

app = Flask(__name__)

# Koneksi ke database MySQL
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="web_crawler"
    )

# Membuat tabel jika belum ada
db = get_db_connection()
cursor = db.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS pages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    url VARCHAR(255),
    title VARCHAR(255),
    paragraph TEXT
)
""")
db.commit()
cursor.close()
db.close()

# Fungsi untuk mengambil halaman dan menyimpannya ke database
visited_urls = set()

def crawl_dfs(url):
    if url in visited_urls:
        return
    visited_urls.add(url)

    response = requests.get(url)
    if response.status_code != 200:
        return

    soup = BeautifulSoup(response.text, "html.parser")
    title = str(soup.title.string) if soup.title and soup.title.string else "No Title"
    paragraph = str(soup.p.get_text()) if soup.p else "No Content"

    # Menyimpan ke database
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("INSERT INTO pages (url, title, paragraph) VALUES (%s, %s, %s)", (url, title, paragraph))
    db.commit()
    cursor.close()
    db.close()

    # Menelusuri semua link di halaman
    for link in soup.find_all("a", href=True):
        next_url = urljoin(url, link['href'])
        crawl_dfs(next_url)

# Flask Route untuk menampilkan tabel hasil crawling
@app.route('/')
def index():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM pages")
    data = cursor.fetchall()
    cursor.close()
    db.close()

    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hasil Web </title>
        <style>
            table { width: 80%; border-collapse: collapse; margin: 20px auto; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f4f4f4; }
            h2 { text-align: center; }
        </style>
    </head>
    <body>
        <h2>Data Hasil Web Crawling</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>URL</th>
                <th>Judul</th>
                <th>Paragraf</th>
            </tr>
            {% for row in data %}
            <tr>
                <td>{{ row.id }}</td>
                <td><a href="{{ row.url }}" target="_blank">{{ row.url }}</a></td>
                <td>{{ row.title }}</td>
                <td>{{ row.paragraph }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    return render_template_string(html_template, data=data)

if __name__ == '__main__':
    # Hapus data lama sebelum crawling baru
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("TRUNCATE TABLE pages")  # Reset database sebelum crawling
    db.commit()
    cursor.close()
    db.close()

    # Memulai crawling dari halaman utama
    start_url = "http://localhost/website_dfs/index.html"  # Sesuaikan dengan URL lokal Anda
    crawl_dfs(start_url)

    print("Crawling selesai. Data disimpan di database.")

    # Menjalankan Flask server
    app.run(debug=True)
