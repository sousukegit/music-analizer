import librosa
import numpy as np
import os
import psycopg2
from ..db.config import DB_CONFIG  # データベース設定をインポート
import sys

def detect_silent_sections(file_path, silence_threshold=-30.0, min_silence_duration=5):
    """
    ボーカルトラックから無音区間（ボーカルがない区間）を検出
    """
    try:
        print(f"Loading file: {file_path}")
        y, sr = librosa.load(file_path, sr=None)

        print("Audio loaded. Calculating energy...")
        frame_length = 2048  # フレームサイズ
        hop_length = 512     # フレームの間隔
        energy = np.array([
            sum(abs(y[i:i+frame_length]**2)) for i in range(0, len(y), hop_length)
        ])

        # デシベルスケールに変換
        energy_db = 10 * np.log10(energy + 1e-6)  # 1e-6はゼロ割防止用
        print("Energy calculated. Converting to dB scale...")

        # 無音フレームの判定
        print("Detecting silence...")
        silence_frames = energy_db < silence_threshold

        # 無音フレームを秒単位でグループ化
        print("Grouping silent sections...")
        silence_times = []
        silence_start = None
        current_silence_duration = 0

        for i, is_silent in enumerate(silence_frames):
            time = i * hop_length / sr  # フレームを秒に変換
            if is_silent:
                if silence_start is None:
                    silence_start = time
                current_silence_duration += hop_length / sr
            else:
                if silence_start is not None:
                    # 無音区間が指定された最小継続時間以上の場合のみ記録
                    if current_silence_duration >= min_silence_duration:
                        silence_end = time
                        silence_times.append([silence_start, silence_end])
                        print(f"Detected silence from {silence_start:.2f}s to {silence_end:.2f}s")
                    # リセット
                    silence_start = None
                    current_silence_duration = 0

        # 最後の無音区間を確認
        if silence_start is not None and current_silence_duration >= min_silence_duration:
            silence_end = len(y) / sr
            silence_times.append([silence_start, silence_end])
            print(f"Detected silence from {silence_start:.2f}s to {silence_end:.2f}s")

        print("Silence detection complete.")
        return silence_times

    except Exception as e:
        print(f"An error occurred: {e}")
        raise

def insert_soro_records(song_id, silence_sections):
    """
    検出された無音区間をsoroテーブルに挿入する。ただし、既存のレコードと重複しないようにする。
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 既存の無音区間を取得
        cursor.execute("""
            SELECT start_time, end_time FROM "Soro" WHERE song_id = %s
        """, (song_id,))
        existing_sections = cursor.fetchall()

        insert_query = """
            INSERT INTO "Soro" (song_id, start_time, end_time, is_guitar_soro, guitar_score)
            VALUES (%s, %s, %s, %s, %s)
        """
        new_records_count = 0
        for section in silence_sections:
            start_time, end_time = section
            # 重複チェック
            is_duplicate = False
            for existing_start, existing_end in existing_sections:
                if (start_time == existing_start and end_time == existing_end) or \
                   (start_time >= existing_start and start_time <= existing_end) or \
                   (end_time >= existing_start and end_time <= existing_end):
                    is_duplicate = True
                    print(f"重複している区間: {start_time} - {end_time}")
                    break

            if not is_duplicate:
                cursor.execute(insert_query, (song_id, start_time, end_time, False, None))
        conn.commit()
        print(f"soroテーブルに{len(silence_sections)}件のレコードを挿入しました。")
    except Exception as e:
        print(f"データベースへの挿入中にエラーが発生しました: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def extract_song_id(folder_name):
    """
    フォルダ名からsong_idを抽出する
    フォルダ名の形式は'songid_曲名'と仮定
    """
    try:
        song_id_str = folder_name.split('_')[0]
        song_id = int(song_id_str)
        return song_id
    except (IndexError, ValueError) as e:
        print(f"フォルダ名 '{folder_name}' からsong_idを抽出できませんでした: {e}")
        return None

def process_all_vocal_files():
    """
    実行日のYYYYMMDDに基づいてhtdemucs_6s配下の全てのvocals.mp3ファイルを処理
    """
    from datetime import datetime
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'../../music/separated/{datetime.now().strftime("%Y%m%d")}/htdemucs_6s')
    print(f"base_dir: {base_dir}")
    # htdemucs_6s配下のフォルダを走査
    for folder in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder)
        if os.path.isdir(folder_path):
            vocals_file = os.path.join(folder_path, 'vocals.wav')
            if os.path.exists(vocals_file):
                print(f"\nProcessing vocals in folder: {folder}")
                try:
                    silent_sections = detect_silent_sections(vocals_file, silence_threshold=0, min_silence_duration=5)
                    print(f"\nDetected silent sections in {folder}:")
                    for start, end in silent_sections:
                        print(f"Start: {start:.2f}s, End: {end:.2f}s")
                    
                    # フォルダ名からsong_idを抽出
                    song_id = extract_song_id(folder)
                    if song_id is None:
                        print(f"song_idの取得に失敗したため、{folder}の処理をスキップします。")
                        continue
                    
                    # データベースに挿入
                    insert_soro_records(song_id, silent_sections)
                    
                except Exception as e:
                    print(f"{folder}の処理に失敗しました: {e}")
        else:
            print(f"フォルダ {folder} が見つかりません。")

def main():
    try:
        process_all_vocal_files()
        return 0  # 正常終了
    except Exception as e:
        print(f"間奏区間分析でエラーが発生しました: {e}")
        return 1  # エラー終了

if __name__ == "__main__":
    sys.exit(main())
