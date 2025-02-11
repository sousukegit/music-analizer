import sys
import subprocess
from pathlib import Path

def run_script(script_path):
    try:
        result = subprocess.run([sys.executable, script_path], check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False

def main():
    # スクリプトの実行順序を定義
    scripts = [
        "app.scripts.download.getpass.py",
        "app.scripts.download.download.py",
        "app.scripts.separate.separate.py",
        "app.scripts.analyze.duration_analyze.py",
        "app.scripts.analyze.is_guitar_analyze_duration.py"
    ]

    # 各スクリプトを順番に実行
    for script in scripts:
        script_path = Path(script)
        if not script_path.exists():
            print(f"エラー: {script} が見つかりません")
            sys.exit(1)

        print(f"実行中: {script}")
        if not run_script(script_path):
            print(f"エラー: {script} の実行に失敗しました")
            sys.exit(1)
        print(f"完了: {script}")

    print("全てのスクリプトの実行が完了しました")

if __name__ == "__main__":
    main()