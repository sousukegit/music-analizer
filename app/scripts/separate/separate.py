import subprocess
import os
import psycopg2
from ..db.config import DB_CONFIG
import time  # リトライ間隔のために time をインポート
import sys

def update_separation_status(song_id):
    """
    曲の分離状態をデータベースで更新する
    
    Args:
        song_id (int): 更新する曲のID
    """
    try:


        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE "Song" 
            SET is_separated = TRUE 
            WHERE song_id = %s
        """, (song_id,))
        
        conn.commit()
        print(f"Song ID {song_id}の分離状態を更新しました")
        
    except Exception as e:
        print(f"データベース更新エラー: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def run_demucs(input_file, output_name="htdemucs_6s"):
    """
    Demucs コマンドを実行し、音声ファイルを処理する関数です。
    
    Args:
        input_file (str): 入力音声ファイルのパス
        song_id (int): 処理する曲のID
        output_name (str): Demucs の出力名
    """

    try:
        # 出力先ディレクトリを作成
        from datetime import datetime
        base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                f'../../music/separated/{datetime.now().strftime("%Y%m%d")}')
        os.makedirs(base_dir, exist_ok=True)

        # Demucs コマンドの構築
        command = [
            "demucs",
            "--name", output_name,
            "--out", base_dir,
            input_file
        ]

        song_id = extract_song_id(input_file)
        
        print(f"Running command: {' '.join(command)}")
        # コマンドの実行
        subprocess.run(command, check=True)
        print("Demucs processing completed successfully.")
        
        # 分離処理が成功したらデータベースを更新
        update_separation_status(song_id)
        # 成功したらループを抜ける

    
    except subprocess.CalledProcessError as e:
        print(f"Error: Demucs failed with return code {e.returncode}. リトライします...")
    except FileNotFoundError:
        print("Error: Demucs is not installed or not in the PATH. リトライします...")
    except Exception as e:
        print(f"An unexpected error occurred: {e}. リトライします...")
        


def extract_song_id(folder_name):
    """
    フォルダ名からsong_idを抽出する
    フォルダ名の形式は'songid_曲名'と仮定
    """
    try:
        file_name = os.path.basename(folder_name)
        song_id_str = file_name.split('_')[0]
        song_id = int(song_id_str)
        return song_id
    except (IndexError, ValueError) as e:
        print(f"フォルダ名 '{folder_name}' からsong_idを抽出できませんでした: {e}")
        return None

def process_all_audio_files():
    """
    Process all WAV files in the downloaded music directory
    """
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../music/downloaded')
    
    # 日付フォルダを走査
    from datetime import datetime
    today = datetime.now().strftime("%Y%m%d")
    date_path = os.path.join(base_dir, today)
    if os.path.isdir(date_path):
        # 当日の日付フォルダ内のWAVファイルを探す
        for file in os.listdir(date_path):
            if file.endswith('.wav'):
                wav_path = os.path.join(date_path, file)
                print(f"Processing: {wav_path}")
                run_demucs(wav_path)
    else:
        print(f"Error: {date_path} is not found.")

def main():
    try:
        process_all_audio_files()
        return 0  # 正常終了
    except Exception as e:
        print(f"分離処理でエラーが発生しました: {e}")
        return 1  # エラー終了

if __name__ == "__main__":
    sys.exit(main())
