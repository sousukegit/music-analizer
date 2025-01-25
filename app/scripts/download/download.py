import subprocess
import json
import os
import re

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
        "--write-thumbnail",  # サムネイルを保存
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
            final_dir = os.path.join(base_output_path, title)
            # os.makedirs(final_dir, exist_ok=True)

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

# メイン処理
def main():
    url = "https://music.youtube.com/watch?v=KAaUyVJoNAE"  # ダウンロード対象のURLを指定
    # スクリプトのディレクトリを基準に相対パスを設定
    base_output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../music/downloaded')
    
    # 一時ディレクトリを作成（存在しない場合）
    os.makedirs(f"{base_output_path}/temp", exist_ok=True)

    # 動画をWAV形式でダウンロードし、サムネイルも保存
    download_and_convert_to_wav_with_thumbnail(url, base_output_path)

    # メタデータを表示
    show_metadata(base_output_path)

if __name__ == "__main__":
    main()
