import os
from config import DB_CONFIG
import psycopg2
from datetime import datetime

def export_current_tables():
    """現在のデータベースのテーブル情報をテキストファイルにエクスポートする"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()

        # スキーマ情報を保存するディレクトリ
        export_dir = os.path.join(os.path.dirname(__file__), 'tables')
        os.makedirs(export_dir, exist_ok=True)

        # 現在の日時でファイル名を生成
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        export_file = os.path.join(export_dir, f'tables_{timestamp}.txt')

        with open(export_file, 'w', encoding='utf-8') as f:
            f.write("=== 現在のテーブル一覧 ===\n\n")
            for table in tables:
                f.write(f"テーブル名: {table[0]}\n")
                # 各テーブルのカラム情報を取得
                cursor.execute(f"""
                    SELECT 
                        column_name, 
                        data_type, 
                        column_default,
                        is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = '{table[0]}'
                    ORDER BY ordinal_position
                """)
                columns = cursor.fetchall()
                f.write("カラム情報:\n")
                for column in columns:
                    col_name, data_type, default, nullable = column
                    f.write(f"  - {col_name}: {data_type}")
                    if default:
                        f.write(f" (デフォルト: {default})")
                    f.write(f" {'NULL許容' if nullable == 'YES' else 'NOT NULL'}\n")
                
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
                        AND tc.table_name = '{table[0]}'
                """)
                foreign_keys = cursor.fetchall()

                if foreign_keys:
                    f.write("外部キー制約:\n")
                    for fk in foreign_keys:
                        col, ref_table, ref_col = fk
                        f.write(f"  - {col} -> {ref_table}({ref_col})\n")
                f.write("\n")
        
        print(f"テーブル情報を保存しました: {export_file}")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def main():
    export_current_tables()

if __name__ == "__main__":
    main()