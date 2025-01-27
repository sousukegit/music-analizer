from dotenv import load_dotenv
import os
import psycopg2
from datetime import datetime

# .envファイルから環境変数を読み込む
load_dotenv()

# データベース接続情報
DB_CONFIG = {
    "dbname": os.environ["POSTGRES_DB"],
    "user": os.environ["POSTGRES_USER"], 
    "password": os.environ["POSTGRES_PASSWORD"],
    "host": "localhost",
    "port": 5432
} 

def export_schema_to_file():
    """現在のデータベーススキーマをテキストファイルにエクスポートする"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # テーブル一覧を取得
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()

        # スキーマ情報を保存するディレクトリ
        schema_dir = os.path.join(os.path.dirname(__file__), 'db/schema')
        os.makedirs(schema_dir, exist_ok=True)

        # 現在の日時でファイル名を生成
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        schema_file = os.path.join(schema_dir, f'schema_{timestamp}.txt')

        with open(schema_file, 'w', encoding='utf-8') as f:
            for table in tables:
                table_name = table[0]
                f.write(f"\n=== Table: {table_name} ===\n")

                # カラム情報を取得
                cursor.execute(f"""
                    SELECT 
                        column_name, 
                        data_type, 
                        column_default,
                        is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position
                """)
                columns = cursor.fetchall()

                for column in columns:
                    col_name, data_type, default, nullable = column
                    f.write(f"{col_name}: {data_type}")
                    if default:
                        f.write(f" (default: {default})")
                    f.write(f" {'NULL' if nullable == 'YES' else 'NOT NULL'}\n")

                # 外部キー制約を取得
                cursor.execute(f"""
                    SELECT
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_name = '{table_name}'
                """)
                foreign_keys = cursor.fetchall()

                if foreign_keys:
                    f.write("\nForeign Keys:\n")
                    for fk in foreign_keys:
                        col, ref_table, ref_col = fk
                        f.write(f"  {col} -> {ref_table}({ref_col})\n")
                
                f.write("\n")

        print(f"スキーマ情報を保存しました: {schema_file}")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close() 