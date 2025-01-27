import psycopg2
from config import DB_CONFIG  # データベース設定をインポート

def check_db_state():
    try:
        # データベースに接続
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("データベースに接続しました。")

        # Songsテーブルの内容を取得
        cursor.execute("SELECT * FROM Songs")
        songs = cursor.fetchall()
        print("Songsテーブルの内容:")
        for song in songs:
            print(song)

        # Artistsテーブルの内容を取得
        cursor.execute("SELECT * FROM Artists")
        artists = cursor.fetchall()
        print("Artistsテーブルの内容:")
        for artist in artists:
            print(artist)

        # 接続を閉じる
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"データベース操作中にエラーが発生しました: {e}")

if __name__ == "__main__":
    check_db_state()