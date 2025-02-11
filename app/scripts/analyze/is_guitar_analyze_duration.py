###関連スコアを合算させてギターの存在を確認する

import os
from decimal import Decimal
import tensorflow as tf
import tensorflow_hub as hub
import librosa
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import logging
import psycopg2
from psycopg2 import sql
from datetime import datetime
import re
from ..db.config import DB_CONFIG  # config.pyからDB設定をインポート
import sys

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# モデルを保存するローカルパス
LOCAL_YAMNET_PATH = 'app/models/yamnet'
YAMNET_MODEL_HANDLE = 'https://tfhub.dev/google/yamnet/1'

def load_yamnet_model(model_handle, local_path=LOCAL_YAMNET_PATH):
    """YAMNetモデルをロード（ローカルに存在しない場合はダウンロード）"""
    
    # ディレクトリが存在しない場合は作成
    os.makedirs(local_path, exist_ok=True)

    # `saved_model.pb` の存在をチェック
    if not os.path.exists(os.path.join(local_path, "saved_model.pb")):
        logging.info("YAMNetモデルをダウンロード中...")
        try:
            yamnet = hub.load(model_handle)
            # モデルを保存（saved_model.pb を含む形式）
            tf.saved_model.save(yamnet, local_path)
            logging.info(f"モデルをローカルに保存しました: {local_path}")
        except Exception as e:
            logging.error(f"モデルのダウンロードまたは保存に失敗しました: {e}")
            raise
    else:
        logging.info(f"ローカルからYAMNetモデルをロードします: {local_path}")
        try:
            yamnet = tf.saved_model.load(local_path)
        except Exception as e:
            logging.error(f"ローカルモデルのロードに失敗しました: {e}")
            raise

    return yamnet

# YAMNetモデルのロード
yamnet = load_yamnet_model(YAMNET_MODEL_HANDLE)
# クラスマップのロード
class_map_path = yamnet.class_map_path().numpy().decode('utf-8')
class_names = list(pd.read_csv(class_map_path)['display_name'])

# ギター関連カテゴリのインデックスを特定
guitar_related_indices = []
try:
    guitar_related_indices = [
        class_names.index('Electric guitar'),
        class_names.index('Guitar'),
        class_names.index('Plucked string instrument')
    ]
    logging.info(f"Guitar-related indices: {guitar_related_indices}")
except ValueError as e:
    logging.error(f"ギター関連カテゴリがクラスマップに存在しません: {e}")
    raise

def load_audio(file_path, target_sr=16000, start_time=None, end_time=None):
    """音声データをロードして16000Hzにリサンプリング。開始時間と終了時間を指定可能"""
    try:
        waveform, sr = librosa.load(file_path, sr=target_sr, offset=start_time, duration=(end_time - start_time) if end_time else None)
        return waveform, sr
    except Exception as e:
        logging.error(f"音声ファイルのロードに失敗しました ({file_path}): {e}")
        raise

def segment_audio(waveform, segment_duration, sr=16000):
    """音声を短いセグメントに分割"""
    segment_samples = int(segment_duration * sr)
    return [waveform[i:i + segment_samples] for i in range(0, len(waveform), segment_samples)]

def detect_guitar_in_segments(audio_file, segment_duration=5, start_time=None, end_time=None):
    """セグメントごとにギター関連カテゴリのスコアを検出。指定された時間範囲内で実行"""
    waveform, sr = load_audio(audio_file, start_time=start_time, end_time=end_time)
    segments = segment_audio(waveform, segment_duration, sr)
    segment_scores = []
    for segment in segments:
        try:
            scores, embeddings, spectrogram = yamnet(segment)
            combined_score = tf.reduce_sum(tf.gather(scores, guitar_related_indices, axis=1), axis=1)
            max_score = tf.reduce_max(combined_score).numpy()
            segment_scores.append(max_score)
        except Exception as e:
            logging.error(f"YAMNet推論中にエラーが発生しました ({audio_file}): {e}")
            segment_scores.append(0)
    return segment_scores, segment_duration

def visualize_combined_scores(all_segment_scores, segment_duration):
    """セグメントごとの統合スコアをプロット"""
    plt.figure(figsize=(15, 5))
    for audio_file, segment_scores in all_segment_scores.items():
        time_bins = np.arange(len(segment_scores)) * segment_duration
        plt.bar(time_bins, segment_scores, width=segment_duration, alpha=0.7, label=os.path.basename(os.path.dirname(audio_file)))
    plt.xlabel("Time (s)")
    plt.ylabel("Score")
    plt.title("Guitar-related Scores Across Segments")
    plt.legend()
    plt.show()

def extract_song_id(file_path):
    """
    ファイルパスからsong_idを抽出する。
    パスの形式: app/music/separated/YYYYMMDD/htdemucs_6s/songid__曲名/guitar.wav
    """
    try:
        # 親ディレクトリの名前を取得
        parent_dir = os.path.dirname(file_path)
        folder_name = os.path.basename(parent_dir)
        
        song_id_str = folder_name.split('__')[0]
        song_id = int(song_id_str)
        logging.info(f"Extracted song_id: {song_id} from folder: {folder_name}")
        return song_id
    except (IndexError, ValueError) as e:
        logging.error(f"フォルダ名 '{folder_name}' からsong_idを抽出できませんでした: {e}")
        raise ValueError(f"フォルダ名からsong_idを抽出できませんでした: {folder_name}") from e

def get_guitar_intervals(song_id, connection):
    """
    指定されたsong_idに対応するギターの開始時間と終了時間をDBから取得する。
    """
    try:
        with connection.cursor() as cursor:
            query = sql.SQL("""
                SELECT soro_id, start_time, end_time 
                FROM soro 
                WHERE song_id = %s 
            """)
            cursor.execute(query, (song_id,))
            intervals = cursor.fetchall()
            logging.info(f"song_id {song_id} のギター区間: {intervals}")
            return intervals
    except Exception as e:
        logging.error(f"DBからギター区間の取得中にエラーが発生しました (song_id={song_id}): {e}")
        raise

def update_soro_record(soro_id, is_guitar_detected, guitar_score, connection):
    """
    指定されたsoro_idのレコードを更新して、is_guitar_soroをTrueに設定し、guitar_scoreを保存する。
    """
    try:
        with connection.cursor() as cursor:
            query = sql.SQL("""
                UPDATE soro
                SET is_guitar_soro = %s,
                    guitar_score = %s
                WHERE soro_id = %s
            """)
            is_guitar_soro_value = bool(is_guitar_detected)
            if guitar_score is not None:
                guitar_score_value = Decimal(float(guitar_score))
            else:
                guitar_score_value = None  # ギターが検出されなかった場合はNoneを設定

            cursor.execute(query, (is_guitar_soro_value, guitar_score_value, soro_id))
            logging.info(f"soro_id {soro_id} のレコードを更新しました。is_guitar_soro: {is_guitar_soro_value}, guitar_score: {guitar_score_value}")
    except Exception as e:
        logging.error(f"soro_id {soro_id} のレコード更新中にエラーが発生しました: {e}")
        raise

def main():
    try:
        # データベースに接続
        connection = psycopg2.connect(**DB_CONFIG)
        connection.autocommit = True  # 自動コミットを有効にする
        logging.info("データベースに正常に接続しました。")
    except Exception as e:
        logging.error(f"データベースへの接続に失敗しました: {e}")
        raise

    # 音声ファイルのパス（動的）
    base_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f'../../music/separated/{datetime.now().strftime("%Y%m%d")}/htdemucs_6s'
    )
    audio_files = []
    try:
        if not os.path.exists(base_dir):
            logging.error(f"ベースディレクトリが存在しません: {base_dir}")
            raise FileNotFoundError(f"ベースディレクトリが存在しません: {base_dir}")

        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file == 'guitar.wav':
                    file_path = os.path.join(root, file)
                    if os.path.isfile(file_path):
                        audio_files.append(file_path)
                        logging.info(f"ファイルを追加: {file_path}")
                    else:
                        logging.warning(f"ファイルが存在しませんまたはアクセスできません: {file_path}")

        if not audio_files:
            logging.warning(f"ベースディレクトリ内に'guitar.wav'ファイルが見つかりませんでした: {base_dir}")
            return 0  # 正常終了

        all_segment_scores = {}
        for audio_file in audio_files:
            try:
                # song_idを抽出
                song_id = extract_song_id(audio_file)
                # DBからギター区間を取得
                intervals = get_guitar_intervals(song_id, connection)
                if not intervals:
                    logging.info(f"song_id {song_id} に対応するギター区間がDBに存在しません。")
                    continue

                for interval in intervals:
                    soro_id, start_time, end_time = interval
                    logging.info(f"Processing {audio_file} の時間範囲: {start_time} - {end_time} 秒 (soro_id: {soro_id})")
                    segment_scores, segment_duration = detect_guitar_in_segments(
                        audio_file, 
                        segment_duration=5, 
                        start_time=start_time, 
                        end_time=end_time
                    )
                    key = f"{audio_file} ({start_time}-{end_time}s)"
                    all_segment_scores[key] = segment_scores

                    # 判定結果を出力
                    max_score = max(segment_scores)
                    is_guitar_detected = max_score > 0.5  # 最大スコアが0.5以上ならギターが存在
                    if is_guitar_detected:
                        logging.info(f"指定された時間範囲内でギターが検出されました ({key}) (最大スコア: {max_score:.2f})")
                    else:
                        logging.info(f"指定された時間範囲内でギターは検出されませんでした ({key}) (最大スコア: {max_score:.2f})")

                    # soroレコードを更新
                    update_soro_record(soro_id, is_guitar_detected, max_score, connection)

            except Exception as e:
                logging.error(f"ファイルの処理中にエラーが発生しました ({audio_file}): {e}")

        # スコアの可視化
        if all_segment_scores:
            visualize_combined_scores(all_segment_scores, segment_duration)

        # データベース接続を閉じる
        connection.close()
        logging.info("データベース接続を閉じました。")
        return 0  # 正常終了
    except Exception as e:
        print(f"ギター分析でエラーが発生しました: {e}")
        return 1  # エラー終了

if __name__ == "__main__":
    sys.exit(main())
