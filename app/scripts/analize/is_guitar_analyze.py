import librosa
import numpy as np
import matplotlib.pyplot as plt

def plot_confidence_distribution(magnitudes):
    """
    各フレームでのピッチ信頼度の分布を可視化
    """
    confidence_values = magnitudes[magnitudes > 0].flatten()
    plt.figure(figsize=(8, 6))
    plt.hist(confidence_values, bins=50, color="skyblue", edgecolor="black")
    plt.title("Pitch Confidence Distribution")
    plt.xlabel("Confidence")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.show()
    

def analyze_dominant_pitch(pitches, magnitudes, sr, pitch_confidence_threshold, freq_range=(80, 1500)):
    """
    フレームごとに支配的なピッチを解析し、特定の周波数範囲内で評価
    """
    dominant_pitches = []
    for t in range(pitches.shape[1]):  # フレームごとに処理
        frame_pitches = pitches[:, t]
        frame_magnitudes = magnitudes[:, t]

        # 閾値以上の振幅を持つピッチを取得
        strong_pitches = frame_pitches[(frame_magnitudes > pitch_confidence_threshold) &
                                        (frame_pitches >= freq_range[0]) &
                                        (frame_pitches <= freq_range[1])]
        strong_magnitudes = frame_magnitudes[(frame_magnitudes > pitch_confidence_threshold) &
                                              (frame_pitches >= freq_range[0]) &
                                              (frame_pitches <= freq_range[1])]

        if len(strong_pitches) > 0:
            # 最大振幅を持つピッチを取得
            max_index = np.argmax(strong_magnitudes)
            dominant_pitches.append(strong_pitches[max_index])

    
    # 信頼度分布のプロット
    plot_confidence_distribution(magnitudes)

    return dominant_pitches

def detect_guitar_playing_style_with_dominance(file_path, intervals, frame_duration=0.1, pitch_confidence_threshold=0.6, hnr_threshold=0.6):
    """
    支配的なピッチの解析を加えたギターパートの判定
    """
    try:
        print(f"Loading file: {file_path}")
        y, sr = librosa.load(file_path, sr=None)

        results = []
        frame_length = int(frame_duration * sr)  # フレームサイズ（サンプル数）

        for start_time, end_time in intervals:
            print(f"Analyzing section: {start_time:.2f}s to {end_time:.2f}s")
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            section_audio = y[start_sample:end_sample]

            # 区間をフレームごとに分割
            num_frames = (len(section_audio) // frame_length) + 1
            dominant_pitch_count = 0
            total_frames = 0

            for i in range(num_frames):
                frame_start = i * frame_length
                frame_end = min((i + 1) * frame_length, len(section_audio))
                frame_audio = section_audio[frame_start:frame_end]

                # ハーモニクスとパーカッシブ成分の分離
                harmonic, _ = librosa.effects.hpss(frame_audio)

                # ピッチ解析
                pitches, magnitudes = librosa.piptrack(y=harmonic, sr=sr)

                # 支配的なピッチを取得
                dominant_pitches = analyze_dominant_pitch(pitches, magnitudes, sr, pitch_confidence_threshold)
                dominant_pitch_count += len(dominant_pitches)
                total_frames += 1

            # 平均支配ピッチ数
            avg_dominant_pitch_count = dominant_pitch_count / total_frames
            print(f"Average dominant pitch count: {avg_dominant_pitch_count:.2f}")

            # 判定ロジック
            if avg_dominant_pitch_count <= 2:  # 支配的なピッチ数が少なければ単音引きと判定
                results.append((start_time, end_time, "単音引き"))
            else:
                results.append((start_time, end_time, "コード引き"))

        print("Analysis Results:")
        for start, end, style in results:
            print(f"Interval {start:.2f}s - {end:.2f}s: {style}")
        return results

    except Exception as e:
        print(f"An error occurred: {e}")
        raise


if __name__ == "__main__":
    guitar_file = "/Users/manabe_soichiro/Desktop/practice/demucs_test/separated/htdemucs_6s/KMDT25/guitar.mp3"
    # 事前に指定された間奏の区間
    intervals = [(1.0, 13.0), (20.68, 30.65)]

    try:
        detect_guitar_playing_style_with_dominance(guitar_file, intervals)
    except Exception as e:
        print(f"Failed to process: {e}")
