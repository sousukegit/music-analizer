import psycopg2
from config import DB_CONFIG

def add_release_date():
    try:
        # データベース接続
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # release_dateカラムを追加
        cursor.execute("""
            ALTER TABLE Songs
            ADD COLUMN release_date DATE;
        """)

        # 変更をコミット
        conn.commit()
        print("release_dateカラムを追加しました")

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
    add_release_date() 