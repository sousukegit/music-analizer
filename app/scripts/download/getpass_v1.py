#試験用　hrefの要素を取得することを個々の曲に対して行った（できない）

import json
import time
import csv
import os
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By

# 📌 クッキーを保存した JSON ファイルのパス
COOKIE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../music.youtube.com_cookies.json")

# 📌 出力する CSV ファイル名
CSV_FILE = "videos.csv"

# 📌 YouTube Music のプレイリスト URL
PLAYLIST_URL = "https://music.youtube.com/playlist?list=RDTMAK5uy_nilrsVWxrKskY0ZUpVZ3zpB0u4LwWTVJ4"

# 📌 最新の Chrome ユーザーエージェントを使用
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

def load_cookies(driver, cookie_file):
    """クッキーを Selenium に適用する"""
    try:
        with open(cookie_file, "r", encoding="utf-8") as f:
            cookies = json.load(f)

        print(f"🔑 クッキーの数: {len(cookies)}")

        for cookie in cookies:
            if "sameSite" not in cookie or cookie["sameSite"] not in ["Strict", "Lax", "None"]:
                cookie["sameSite"] = "None"

            try:
                driver.add_cookie(cookie)
            except Exception as e:
                print(f"⚠ クッキー適用エラー: {cookie['name']} - {e}")

        print("✅ クッキーを適用しました")
    
    except Exception as e:
        print("❌ クッキーの読み込みまたは適用に失敗しました")
        traceback.print_exc()

def get_music_video_urls(playlist_url):
    """YouTube Music のプレイリストから動画URLを取得"""

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=False")  # デバッグ用にブラウザを表示（デバッグ後は True に戻す）
    options.add_argument(f"user-agent={USER_AGENT}")  # ユーザーエージェントを最新の Chrome に変更
    options.add_argument("--disable-blink-features=AutomationControlled")  # Selenium の自動操作検知を回避
    options.add_experimental_option("excludeSwitches", ["enable-automation"])  # 自動操作フラグを消す
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)

    try:
        print("🔄 YouTube Music にアクセス中...")
        driver.get("https://music.youtube.com")
        time.sleep(3)  # クッキーを適用するための待機

        print(f"🌐 現在のページタイトル: {driver.title}")
        print(f"📍 現在のURL: {driver.current_url}")

        # クッキーを適用
        load_cookies(driver, COOKIE_FILE)
        driver.refresh()  # クッキー適用後にリロード
        time.sleep(3)

        print(f"📌 プレイリストに移動: {playlist_url}")
        driver.get(playlist_url)
        time.sleep(5)  # 読み込み待機

        print(f"🌐 プレイリストページタイトル: {driver.title}")
        print(f"📍 プレイリストページURL: {driver.current_url}")

        # ページの一部HTMLを表示（デバッグ用）
        print("📜 ページのHTMLの一部:")
        print(driver.page_source[:500])  # 最初の500文字のみ表示

        # YouTube Music のプレイリスト内の動画リンクを取得
        elements = driver.find_elements(By.XPATH, "//a[contains(@href, 'watch?v=')]")
        print(f"🔍 取得したリンクの数: {len(elements)}")

        if not elements:
            print("⚠ 動画リンクが見つかりませんでした")
            driver.save_screenshot("debug_screenshot.png")  # デバッグ用スクリーンショット保存

        # 各動画の URL をリストに格納
        video_urls = [f"https://music.youtube.com{elem.get_attribute('href')}" for elem in elements]
        return video_urls

    except Exception as e:
        print("❌ エラーが発生しました")
        traceback.print_exc()
        return []

    finally:
        driver.quit()

def save_to_csv(video_urls, filename=CSV_FILE):
    """取得した動画URLをCSVファイルに保存"""
    
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["No.", "Video URL"])  # ヘッダー行を書き込む

        for index, url in enumerate(video_urls, start=1):
            writer.writerow([index, url])  # 動画番号とURLを書き込む

    print(f"✅ {filename} に保存しました！")

if __name__ == "__main__":
    # 🎯 プレイリストから動画URLを取得
    video_urls = get_music_video_urls(PLAYLIST_URL)

    # 📥 CSV に保存
    if video_urls:
        save_to_csv(video_urls)
    else:
        print("❌ 動画URLを取得できませんでした。")
