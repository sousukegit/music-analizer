import subprocess
import json
import os
import re
import yt_dlp
from datetime import datetime

# yt-dlpで動画をダウンロードしてWAVファイルに変換し、サムネイルを保存する
def download_and_convert_to_wav_with_thumbnail(url, base_output_path):
    # 一時的なファイル名テンプレート
    temp_template = f"{base_output_path}/temp/%(title)s.%(ext)s"
    
    # yt-dlpコマンド
    command = [
        
        "yt-dlp",
        "-x",  # 音声抽出
        "--audio-format", "wav",  # WAV形式
        "--write-info-json",  # メタデータをJSONファイルに出力
        "--ffmpeg-location", "/opt/homebrew/bin/ffmpeg",
        "-o", temp_template,  # 出力先テンプレート（仮）
        url
    ]
    subprocess.run(command, check=True)

    # 一時ディレクトリ内のファイルを整理
    temp_dir = f"{base_output_path}/temp"
    for file_name in os.listdir(temp_dir):
        # タイトル部分を抽出
        title_match = re.match(r"(.+)\.(wav|info\.json|jpg|png|webp)", file_name)
        if title_match:
            title = title_match.group(1)
            extension = title_match.group(2)

            # 保存先ディレクトリを作成
            today = datetime.now().strftime("%Y%m%d")
            final_dir = os.path.join(base_output_path, today, title)
            os.makedirs(final_dir, exist_ok=True)

            # ファイルを移動
            old_path = os.path.join(temp_dir, file_name)
            new_path = os.path.join(final_dir, file_name)
            os.rename(old_path, new_path)

# メタデータを読み込んで表示する
def show_metadata(base_output_path):
    music_dir = os.path.join(base_output_path, "music")
    for root, dirs, files in os.walk(music_dir):
        for file_name in files:
            if file_name.endswith(".info.json"):
                json_path = os.path.join(root, file_name)
                with open(json_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    print(f"メタデータ ({json_path}):")
                    print(json.dumps(metadata, indent=4, ensure_ascii=False))  # 見やすくフォーマット

class YTDLPDownloader:
    def __init__(self, download_path, ffmpeg_path='/opt/homebrew/bin/ffmpeg'):
        self.download_path = download_path
        self.ffmpeg_path = ffmpeg_path
        self.ydl_opts = {
            'format': 'bestaudio',  # 音声の品質はデフォルト
            'outtmpl': f"{self.download_path}/temp/%(title)s.%(ext)s",
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'ffmpeg_location': self.ffmpeg_path,
            'quiet': True,
        }
        self.ydl = yt_dlp.YoutubeDL(self.ydl_opts)

    def download_audio(self, url):
        info_dict = self.ydl.extract_info(url, download=True)
        sanitized_info = self.ydl.sanitize_info(info_dict)
        print(json.dumps(sanitized_info, indent=4, ensure_ascii=False))
        return sanitized_info

    def organize_files(self):
        temp_dir = os.path.join(self.download_path, 'temp')
        today = datetime.now().strftime("%Y%m%d")
        final_dir = os.path.join(self.download_path, today)
        os.makedirs(final_dir, exist_ok=True)

        for file_name in os.listdir(temp_dir):
            old_path = os.path.join(temp_dir, file_name)
            new_path = os.path.join(final_dir, file_name)
            os.rename(old_path, new_path)

# メイン処理
def main():
    url = "https://music.youtube.com/watch?v=KAaUyVJoNAE"
    base_output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../music/downloaded')
    downloader = YTDLPDownloader(base_output_path)
    downloader.download_audio(url)
    downloader.organize_files()

if __name__ == "__main__":
    main()
