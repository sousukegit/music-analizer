import psycopg2
from config import DB_CONFIG
from export_table import export_current_tables

def add_is_separated():
    try:
        # データベース接続
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # is_separatedカラムを追加（デフォルトはFalse）
        cursor.execute("""
            ALTER TABLE songs
            ADD COLUMN is_separated BOOLEAN DEFAULT FALSE NOT NULL;
        """)

        # 変更をコミット
        conn.commit()
        print("is_separatedカラムを追加しました")

        # テーブル情報をエクスポート
        export_current_tables()

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
    add_is_separated() 