import subprocess
import sys
import os
import re
import yt_dlp
from datetime import datetime
import json
import psycopg2  # PostgreSQL接続用のライブラリをインポート



from ..db.config import DB_CONFIG  # データベース設定をインポート


class YTDLPDownloader:
    def __init__(self, download_path, ffmpeg_path='/opt/homebrew/bin/ffmpeg', cookies_file='../../../music.youtube.com_cookies.txt'):
        self.download_path = download_path
        self.ffmpeg_path = ffmpeg_path
        self.cookies_file = cookies_file
        self.ydl_opts = {
            'format': 'bestaudio',  # 音声の品質はデフォルト
            'outtmpl': f"{self.download_path}/temp/%(title)s.%(ext)s",
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'ffmpeg_location': self.ffmpeg_path,
            'quiet': True,  # 詳細なログを出力するためにquietをFalseに設定
            'cookiefile': self.cookies_file,  # クッキーファイルを指定
        }
        self.ydl = yt_dlp.YoutubeDL(self.ydl_opts)

    def download_audio(self, url):
        if not os.path.exists(self.cookies_file):
            print(f"クッキーファイルが存在しません: {self.cookies_file}")
            return None
        info_dict = self.ydl.extract_info(url, download=True)
        sanitized_info = self.ydl.sanitize_info(info_dict)
        return sanitized_info

    def organize_files(self, song_id):
        temp_dir = os.path.join(self.download_path, 'temp')
        today = datetime.now().strftime("%Y%m%d")
        final_dir = os.path.join(self.download_path, today)
        os.makedirs(final_dir, exist_ok=True)

        for file_name in os.listdir(temp_dir):
            old_path = os.path.join(temp_dir, file_name)
            base, ext = os.path.splitext(file_name)
            new_file_name = f"{song_id}__{base}.wav"
            new_path = os.path.join(final_dir, new_file_name)
            os.rename(old_path, new_path)
            print(f"ファイルをリネームしました: {old_path} → {new_path}")

    def insert_metadata_into_db(self, metadata):
        # 必要な項目を取得
        youtube_music_id = metadata.get('id')
        title = metadata.get('title')
        artist_name = metadata.get('artist')
        duration = metadata.get('duration')
        url = metadata.get('webpage_url')
        release_date_str = metadata.get('release_date')
        release_date = datetime.strptime(release_date_str, '%Y%m%d').date() if release_date_str else None
            
        try:
            # データベースに接続
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            print(f"データベースに接続しました: {conn}")

            # Artistsテーブルにアーティストを挿入または存在確認
            cursor.execute("SELECT artist_id FROM Artists WHERE english_name = %s", (artist_name,))
            artist = cursor.fetchone()
            print(f"アーティストの取得: {artist}")
            if artist:
                artist_id = artist[0]
            else:
                cursor.execute("INSERT INTO Artists (english_name) VALUES (%s) RETURNING artist_id", (artist_name,))
                artist_id = cursor.fetchone()[0]
            print(f"アーティストの挿入: {artist_id}")
            
            # Songsテーブルに曲を挿入
            cursor.execute("""
                INSERT INTO Songs (title, duration, youtube_music_id, artist_id, url, release_date)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (youtube_music_id) DO NOTHING
                RETURNING song_id
            """, (title, duration, youtube_music_id, artist_id, url, release_date))

            song = cursor.fetchone()
            if song:
                song_id = song[0]
                print(f"曲が挿入されました。song_id: {song_id}")
            else:
                # 既に存在する場合、song_idを取得
                cursor.execute("SELECT song_id FROM Songs WHERE youtube_music_id = %s", (youtube_music_id,))
                song = cursor.fetchone()
                song_id = song[0] if song else None
                print(f"既存の曲のsong_id: {song_id}")

            # コミットして接続を閉じる
            conn.commit()
            cursor.close()
            conn.close()

            return song_id  # song_idを返す

        except Exception as e:
            print(f"データベース操作中にエラーが発生しました: {e}")
            if conn:
                conn.rollback()
                print("ロールバックが完了しました。")
            return None


# メイン処理
def main():
    url = "https://music.youtube.com/watch?v=2WGgkcVBqoc&list=RDTMAK5uy_mZtXeU08kxXJOUhL0ETdAuZTh1z7aAFAo"
    base_output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../music/downloaded')
    downloader = YTDLPDownloader(
        base_output_path, 
        cookies_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../music.youtube.com_cookies.txt')
    )
    metadata = downloader.download_audio(url)
    if metadata:
        song_id = downloader.insert_metadata_into_db(metadata)  # メタデータをデータベースに挿入しsong_idを取得
        if song_id:
            downloader.organize_files(song_id)  # song_idを渡してファイルを整理・リネーム
        else:
            print("song_idの取得に失敗しました。ファイルの整理をスキップします。")

if __name__ == "__main__":
    main()
