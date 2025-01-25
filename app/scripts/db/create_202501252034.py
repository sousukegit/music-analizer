import psycopg2
from psycopg2 import sql

# データベース接続情報
DB_CONFIG = {
    "dbname": "your_database_name",
    "user": "your_username",
    "password": "your_password",
    "host": "localhost",
    "port": 5432
}

# SQLスクリプト：テーブル作成
CREATE_SONGS_TABLE = """
CREATE TABLE IF NOT EXISTS songs (
    song_id SERIAL PRIMARY KEY,                -- 楽曲の一意なID
    title VARCHAR(255) NOT NULL,               -- 楽曲名
    youtube_music_id VARCHAR(255),             -- YouTube Musicの動画ID
    url VARCHAR(255),                          -- 楽曲のURL（汎用的に使用可能）
    duration FLOAT,                            -- 楽曲の長さ（秒）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- レコード作成日時
);
"""

CREATE_SORO_TABLE = """
CREATE TABLE IF NOT EXISTS soro (
    soro_id SERIAL PRIMARY KEY,                -- ギターソロの一意なID
    song_id INTEGER NOT NULL,                  -- songsテーブルの外部キー
    start_time FLOAT NOT NULL,                 -- ソロ部分の開始時間（秒）
    end_time FLOAT NOT NULL,                   -- ソロ部分の終了時間（秒）
    is_guitar_soro BOOLEAN DEFAULT FALSE,      -- ギターソロであるかの真偽値
    guitar_score FLOAT,                        -- ギターソロ判定スコア
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- レコード作成日時
    FOREIGN KEY (song_id) REFERENCES songs(song_id) -- 外部キー制約
);
"""

def create_tables():
    """PostgreSQLデータベースにテーブルを作成する"""
    try:
        # データベース接続
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # テーブル作成
        print("Creating 'songs' table...")
        cursor.execute(CREATE_SONGS_TABLE)
        print("Creating 'soro' table...")
        cursor.execute(CREATE_SORO_TABLE)

        # 変更をコミット
        conn.commit()
        print("Tables created successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # 接続を閉じる
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    create_tables()
