from selenium import webdriver
from selenium.webdriver.common.by import By
import json
import time
import traceback
import csv
import os

# JSON ファイルパス
COOKIE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../music.youtube.com_cookies.json")
CSV_FILE = f"app/csv/{time.strftime('%Y%m%d')}_videos.csv"
# PLAYLIST_URL = "https://music.youtube.com/watch?v=R2nhllG6SKs&list=RDTMAK5uy_mZtXeU08kxXJOUhL0ETdAuZTh1z7aAFAo"
PLAYLIST_URL = "https://music.youtube.com/watch?v=su5oj4X9_AU&list=RDCLAK5uy_m1h6RaRmM8e_3k7ec4ZVJzfo2pXdLrY_k"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# def load_cookies(driver, cookie_file):
#     try:
#         with open(cookie_file, "r", encoding="utf-8") as f:
#             cookies = json.load(f)
#         for cookie in cookies:
#             driver.add_cookie(cookie)
#     except Exception as e:
#         print(f"❌ クッキーの読み込みまたは適用に失敗しました: {e}")

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



def get_playlist_videos(playlist_url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=False")
    options.add_argument(f"user-agent={USER_AGENT}")
    driver = webdriver.Chrome(options=options)
    
    try:
        print("🔄 YouTube Music にアクセス中...")
        driver.get("https://music.youtube.com")
        time.sleep(3)

        print(f"🌐 現在のページタイトル: {driver.title}")
        print(f"📍 現在のURL: {driver.current_url}")

        load_cookies(driver, COOKIE_FILE)
        driver.refresh()
        time.sleep(3)
        
        print(f"📌 プレイリストに移動: {playlist_url}")
        driver.get(playlist_url)
        time.sleep(5)
        
        # プレイリスト内の曲を取得
        items = driver.find_elements(By.CSS_SELECTOR, "ytmusic-player-queue-item")
        print(f"🎵 全体のアイテム数: {len(items)}")

        visible_items = [item for item in items if item.is_displayed()]
        print(f"🎵 表示されているアイテム数: {len(visible_items)}")

        video_data = []
        
        for i, item in enumerate(visible_items):
            try:

                # 非表示の要素はスキップ
                if not item.is_displayed():
                    print(f"⏩ アイテム {i+1} は非表示のためスキップします")
                    continue
                # 曲タイトルを取得

                title_element = item.find_element(By.CSS_SELECTOR, ".song-title")
                title = title_element.get_attribute("title")
                print('song　title', title)
                
                # アーティスト名を取得
                artist_element = item.find_element(By.CSS_SELECTOR, ".byline")
                artist = artist_element.get_attribute("title")
                print('artist', artist)
                # 現在の曲のURL
                play_button = item.find_element(By.CSS_SELECTOR, "#play-button")
                play_button.click()
                time.sleep(3)
                current_url = driver.current_url
                
                print(f"✅ 曲: {title}, アーティスト: {artist}, URL: {current_url}")
                video_data.append({"title": title, "artist": artist, "url": current_url})
            except Exception as e:
                print(f"⚠ 曲の取得でエラー: {e}")
                driver.save_screenshot(f"error_{i+1}.png")


                traceback.print_exc()

        return video_data

    finally:
        driver.quit()

def save_to_csv(video_data, filename=CSV_FILE):
    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["title", "artist", "url"])
            writer.writeheader()
            writer.writerows(video_data)
        print(f"✅ {filename} に保存しました！")
    except Exception as e:
        print(f"❌ CSV ファイルへの保存中にエラーが発生しました: {e}")

if __name__ == "__main__":
    videos = get_playlist_videos(PLAYLIST_URL)
    if videos:
        save_to_csv(videos)
    else:
        print("❌ 動画データが取得できませんでした。")
