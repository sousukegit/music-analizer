import subprocess
import os

def run_demucs(input_file, output_name="htdemucs_6s"):
    """
    Runs the Demucs command to process an audio file.
    
    Args:
        input_file (str): Path to the input audio file.
        output_name (str): Name for the Demucs output.
        format (str): Output format (e.g., wav).
    """
    try:
        # 出力先ディレクトリを作成
        from datetime import datetime
        base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'../../music/separated/{datetime.now().strftime("%Y%m%d")}')
        os.makedirs(base_dir, exist_ok=True)

        # Build the Demucs command
        command = [
            "demucs",
            "--name", output_name,
            "--out", base_dir,
            input_file
        ]
        
        print(f"Running command: {' '.join(command)}")
        # Run the command
        subprocess.run(command, check=True)
        print("Demucs processing completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error: Demucs failed with return code {e.returncode}.")
    except FileNotFoundError:
        print("Error: Demucs is not installed or not in the PATH.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

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

if __name__ == "__main__":
    process_all_audio_files()
