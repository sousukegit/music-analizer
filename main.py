import sys
import subprocess

def run_script(module_name):
    try:
        result = subprocess.run(["pipenv", "run", "python", "-m", module_name], check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False

def main():
    # スクリプトの実行順序を定義
    scripts = [
        "app.scripts.download.getpass",
        "app.scripts.download.download",
        "app.scripts.separate.separate",
        "app.scripts.analyze.duration_analyze",
        "app.scripts.analyze.is_guitar_analyze_duration"
    ]

    # 各スクリプトを順番に実行
    for script in scripts:
        print(f"実行中: {script}")
        if not run_script(script):
            print(f"エラー: {script} の実行に失敗しました")
            sys.exit(1)
        print(f"完了: {script}")

    print("全てのスクリプトの実行が完了しました")

if __name__ == "__main__":
    main()