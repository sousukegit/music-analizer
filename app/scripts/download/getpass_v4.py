import json
import time
import csv
import os
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# 📌 クッキーを保存した JSON ファイルのパス
COOKIE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../music.youtube.com_cookies.json")

# 📌 出力する CSV ファイル名
CSV_FILE = "videos.csv"

# 📌 YouTube Music のプレイリスト URL
PLAYLIST_URL = "https://music.youtube.com/watch?v=xwXAh4gxMbM&list=RDTMAK5uy_nTsa0Irmcu2li2-qHBoZxtrpG9HuC3k_Q"

# 📌 最新の Chrome ユーザーエージェント
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

def load_cookies(driver, cookie_file):
    """クッキーを Selenium に適用する"""
    try:
        with open(cookie_file, "r", encoding="utf-8") as f:
            cookies = json.load(f)

        for cookie in cookies:
            if "sameSite" not in cookie or cookie["sameSite"] not in ["Strict", "Lax", "None"]:
                cookie["sameSite"] = "None"
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                print(f"⚠ クッキー適用エラー: {cookie['name']} - {e}")
    except Exception as e:
        print("❌ クッキーの読み込みまたは適用に失敗しました")
        traceback.print_exc()

def get_music_video_urls(playlist_url):
    """YouTube Music のプレイリストから動画URLを取得"""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=False")  # デバッグ用にブラウザを表示
    options.add_argument(f"user-agent={USER_AGENT}")  # ユーザーエージェント
    options.add_argument("--disable-blink-features=AutomationControlled")  # 自動検知回避
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)

    try:
        print("🔄 YouTube Music にアクセス中...")
        driver.get("https://music.youtube.com")
        time.sleep(3)

        # クッキー適用
        load_cookies(driver, COOKIE_FILE)
        driver.refresh()
        time.sleep(3)

        driver.get(playlist_url)
        time.sleep(5)

        video_urls = []
        action = ActionChains(driver)
        items = driver.find_elements(By.CSS_SELECTOR, "ytmusic-player-queue-item")
        print(f"🎵 取得した曲の数: {len(items)}")

        for i, item in enumerate(items):
            try:
                print(f"🎶 {i+1}曲目を操作中...")

                # サムネイルにマウスをかざす（マウスホバー動作）
                action.move_to_element(item).perform()
                time.sleep(1)

                # 再生ボタンをクリック
                play_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "ytmusic-play-button-renderer")
                    )
                )
                play_button.click()
                time.sleep(3)

                # 現在のURLを取得
                video_url = driver.current_url
                print(f"✅ 再生中のURL: {video_url}")
                video_urls.append(video_url)
            except Exception as e:
                print(f"⚠ {i+1}曲目でエラー: {e}")
                driver.save_screenshot(f"error_{i+1}.png")
                continue

        return video_urls

    except Exception as e:
        print("❌ 全体エラーが発生しました")
        traceback.print_exc()
        return []

    finally:
        driver.quit()

def save_to_csv(video_urls, filename=CSV_FILE):
    """取得した動画URLをCSVファイルに保存"""
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["No.", "Video URL"])
        for index, url in enumerate(video_urls, start=1):
            writer.writerow([index, url])
    print(f"✅ {filename} に保存しました！")

if __name__ == "__main__":
    video_urls = get_music_video_urls(PLAYLIST_URL)
    if video_urls:
        save_to_csv(video_urls)
    else:
        print("❌ 動画URLを取得できませんでした。")
