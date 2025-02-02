import psycopg2
from config import DB_CONFIG


def update_youtube_music_id():
    try:
        # データベース接続
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # youtube_music_idにユニーク制約を追加
        cursor.execute("""
            ALTER TABLE Songs
            ADD CONSTRAINT unique_youtube_music_id UNIQUE (youtube_music_id);
        """)

        # 変更をコミット
        conn.commit()
        print("youtube_music_idにユニーク制約を追加しました")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        conn.rollback()
    finally:
        # 接続を閉じる
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    update_youtube_music_id()