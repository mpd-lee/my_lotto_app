import pandas as pd
import sqlite3
import os

def create_db_from_excel():
    excel_file = "로또 회차별 당첨번호_20260919204905.xlsx"
    
    print("🚀 엑셀 파일에서 당첨 번호 데이터를 읽어오는 중입니다...")
    
    if not os.path.exists(excel_file):
        print(f"❌ '{excel_file}' 파일을 찾을 수 없습니다.")
        return

    try:
        df = pd.read_excel(excel_file)
        df_clean = df[['회차', '당첨번호', 'Unnamed: 3', 'Unnamed: 4', 'Unnamed: 5', 'Unnamed: 6', 'Unnamed: 7', '보너스']].copy()
        df_clean.columns = ['drw_no', 'num1', 'num2', 'num3', 'num4', 'num5', 'num6', 'bonus']
        
        for col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
            
        df_clean = df_clean.dropna().sort_values(by='drw_no', ascending=True).reset_index(drop=True)
        
        conn = sqlite3.connect("lotto_history.db")
        df_clean.to_sql("lotto_results", conn, if_exists="replace", index=False)
        conn.close()
        
        print(f"✅ 성공! 총 {len(df_clean)}개 회차의 데이터가 'lotto_history.db'에 저장되었습니다.")
        
    except Exception as e:
        print(f"⚠️ 엑셀 변환 중 오류 발생: {e}")

if __name__ == "__main__":
    create_db_from_excel()