###関連スコアを合算させてギターの存在を確認する

import tensorflow as tf
import tensorflow_hub as hub
import librosa
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# YAMNetモデルのロード
yamnet_model_handle = 'https://tfhub.dev/google/yamnet/1'
yamnet = hub.load(yamnet_model_handle)

# クラスマップのロード
class_map_path = yamnet.class_map_path().numpy().decode('utf-8')
class_names = list(pd.read_csv(class_map_path)['display_name'])

# ギター関連カテゴリのインデックスを特定
guitar_related_indices = [
    class_names.index('Electric guitar'),
    class_names.index('Guitar'),
    class_names.index('Plucked string instrument')
]
print(f"Guitar-related indices: {guitar_related_indices}")

def load_audio(file_path, target_sr=16000, start_time=None, end_time=None):
    """音声データをロードして16000Hzにリサンプリング。開始時間と終了時間を指定可能"""
    waveform, sr = librosa.load(file_path, sr=target_sr, offset=start_time, duration=(end_time - start_time) if end_time else None)
    return waveform, sr

def segment_audio(waveform, segment_duration, sr=16000):
    """音声を短いセグメントに分割"""
    segment_samples = int(segment_duration * sr)
    return [waveform[i:i + segment_samples] for i in range(0, len(waveform), segment_samples)]

def detect_guitar_in_segments(audio_file, segment_duration=5, start_time=None, end_time=None):
    """セグメントごとにギター関連カテゴリのスコアを検出。指定された時間範囲内で実行"""
    # 音声データをロード（指定された時間範囲を考慮）
    waveform, sr = load_audio(audio_file, start_time=start_time, end_time=end_time)

    # 音声をセグメントに分割
    segments = segment_audio(waveform, segment_duration, sr)

    segment_scores = []
    for segment in segments:
        # YAMNetに入力して推論
        scores, embeddings, spectrogram = yamnet(segment)
        # ギター関連カテゴリのスコアを抽出して合算
        combined_score = tf.reduce_sum(tf.gather(scores, guitar_related_indices, axis=1), axis=1)
        # セグメント内の最大スコアを取得
        max_score = tf.reduce_max(combined_score).numpy()
        segment_scores.append(max_score)

    return segment_scores, segment_duration


def visualize_combined_scores(segment_scores, segment_duration):
    """セグメントごとの統合スコアをプロット"""
    time_bins = np.arange(len(segment_scores)) * segment_duration

    plt.figure(figsize=(15, 5))
    plt.bar(time_bins, segment_scores, width=segment_duration, color='blue', alpha=0.7, label="Guitar-related scores")
    plt.xlabel("Time (s)")
    plt.ylabel("Score")
    plt.title("Guitar-related Scores Across Segments")
    plt.legend()
    plt.show()

def main():
    # 音声ファイルのパス（固定）
    audio_file = '/Users/manabe_soichiro/Desktop/practice/guitar-batch/app/music/separated/20250201/htdemucs_6s/6__光の中へ/guitar.mp3'

    # 判定する時間範囲（例: 10秒から30秒まで）
    start_time = 5  # 開始時間（秒）
    end_time = 10    # 終了時間（秒）

    # セグメント解析
    segment_duration = 5  # セグメントの長さ（秒単位）
    segment_scores, segment_duration = detect_guitar_in_segments(audio_file, segment_duration, start_time, end_time)

    # 判定結果を出力
    max_score = max(segment_scores)
    if max_score > 0.5:  # 最大スコアが0.5以上ならギターが存在
        print(f"指定された時間範囲内でギターが検出されました (最大スコア: {max_score:.2f})")
    else:
        print(f"指定された時間範囲内でギターは検出されませんでした (最大スコア: {max_score:.2f})")

    # スコアの可視化
    visualize_combined_scores(segment_scores, segment_duration)

if __name__ == "__main__":
    main()
