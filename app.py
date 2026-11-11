import time
import sqlite3
import requests
from bs4 import BeautifulSoup

# ==========================================
# 1. スクレイピング（自動データ収集）関数
# ==========================================
def scrape_google_repos():
    # Googleのリポジトリ一覧ページ
    url = "https://github.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print("GitHub（Google）からデータを集めています...")
    response = requests.get(url, headers=headers)
    
    # 課題のルール：アクセス直後に必ず sleep(1) を入れる
    time.sleep(1)
    
    if response.status_code != 200:
        print(f"エラーが発生しました（ステータスコード: {response.status_code}）")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    repos_data = []

    # GitHubのHTML構造（リポジトリの各行）を見つけてループを回す
    repo_list = soup.find_all('li', class_='col-12 d-flex flex-justify-between width-full py-4 border-bottom color-border-muted public source')
    if not repo_list:
        # クラス名が異なる場合の予備ルート
        repo_list = soup.find_all('li', itemprop='owns')

    for li in repo_list:
        try:
            # 1. リポジトリ名
            name_tag = li.find('a', itemprop='name codeRepository')
            name = name_tag.text.strip() if name_tag else "Unknown"
            
            # 2. 主要な言語
            lang_tag = li.find('span', itemprop='programmingLanguage')
            lang = lang_tag.text.strip() if lang_tag else "Unknown"
            
            # 3. スターの数
            star_tag = li.find('a', href=lambda x: x and '/stargazers' in x)
            if star_tag:
                star_text = star_tag.text.strip().replace(',', '')
                stars = int(star_text)
            else:
                stars = 0
            
            repos_data.append((name, lang, stars))
        except Exception:
            continue

    return repos_data

# ==========================================
# 2. データベース（SQLite）操作関数
# ==========================================
def save_to_database(data):
    # データベースファイル（google_repos.db）を作成して接続
    conn = sqlite3.connect('google_repos.db')
    cursor = conn.cursor()
    
    # すでにテーブルがあれば一旦削除して新しく作り直す
    cursor.execute('DROP TABLE IF EXISTS repositories')
    
    # テーブルの作成（id、リポジトリ名、言語、スター数）
    cursor.execute('''
        CREATE TABLE repositories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            language TEXT,
            stars INTEGER
        )
    ''')
    
    # データの挿入（まとめて安全に保存する）
    cursor.executemany('''
        INSERT INTO repositories (name, language, stars)
        VALUES (?, ?, ?)
    ''', data)
    
    conn.commit()
    print(f"【成功】{len(data)} 件のデータをデータベースに保存しました。")
    conn.close()

# ==========================================
# 3. SELECT文でデータを画面に表示する関数
# ==========================================
def display_data():
    conn = sqlite3.connect('google_repos.db')
    cursor = conn.cursor()
    
    # 課題のルール：SELECT文を使ってデータを取得して表示
    cursor.execute('SELECT name, language, stars FROM repositories ORDER BY stars DESC')
    rows = cursor.fetchall()
    
    print("\n====== データベースから取得した結果（SELECT文） ======")
    for row in rows:
        print(f"リポジトリ名: {row[0]:<30} | 言語: {row[1]:<12} | スター数: {row[2]}")
    print("======================================================")
        
    conn.close()

# ==========================================
# メイン処理の実行
# ==========================================
if __name__ == "__main__":
    # 1. データを集める
    scraped_data = scrape_google_repos()
    
    # ネットワークエラー等でデータが取れなかった場合のテスト用バックアップデータ
    if not scraped_data:
        print("※スクレイピングでデータが取得できなかったため、テスト用データを生成します。")
        scraped_data = [
            ("gson", "Java", 24000),
            ("guava", "Java", 49000),
            ("angular", "TypeScript", 95000),
            ("flutter", "Dart", 160000),
            ("jax", "Python", 31000)
        ]
        
    # 2. データベースに保存
    save_to_database(scraped_data)
    
    # 3. SELECT文で確認表示
    display_data()
