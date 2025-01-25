import librosa
import numpy as np
import os

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

        # デバッグログを追加（フレームごとの音量を表示）
        for i, energy_value in enumerate(energy_db):
            time = i * hop_length / sr
            # print(f"Time: {time:.2f}s, Energy (dB): {energy_value:.2f}, Silent: {energy_value < silence_threshold}")

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

def process_all_vocal_files():
    """
    htdemucs_6s配下の全てのvocals.mp3ファイルを処理
    """
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../music/separated/htdemucs_6s')
    
    # htdemucs_6s配下のフォルダを走査
    for folder in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder)
        if os.path.isdir(folder_path):
            vocals_file = os.path.join(folder_path, 'vocals.mp3')
            if os.path.exists(vocals_file):
                print(f"\nProcessing vocals in folder: {folder}")
                try:
                    silent_sections = detect_silent_sections(vocals_file, silence_threshold=0, min_silence_duration=5)
                    print(f"\nDetected silent sections in {folder}:")
                    for start, end in silent_sections:
                        print(f"Start: {start:.2f}s, End: {end:.2f}s")
                except Exception as e:
                    print(f"Failed to process {folder}: {e}")

if __name__ == "__main__":
    process_all_vocal_files()
