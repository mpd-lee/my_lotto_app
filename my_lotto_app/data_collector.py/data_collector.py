import os
import requests
import pandas as pd

CSV_FILE = "lotto_data.csv"

def get_lotto_data(drw_no):
    """동행복권 공식 API에서 특정 회차 당첨 번호 및 통계 데이터 조회 (User-Agent 헤더 추가)"""
    url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={drw_no}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code != 200:
            return None
        
        # JSON 형식인지 안전하게 확인 후 파싱
        data = res.json()
        if data.get("returnValue") == "success":
            return {
                "drwNo": data.get("drwNo"),
                "drwNoDate": data.get("drwNoDate"),
                "drwtNo1": data.get("drwtNo1"),
                "drwtNo2": data.get("drwtNo2"),
                "drwtNo3": data.get("drwtNo3"),
                "drwtNo4": data.get("drwtNo4"),
                "drwtNo5": data.get("drwtNo5"),
                "drwtNo6": data.get("drwtNo6"),
                "bnusNo": data.get("bnusNo"),
                "totSellamnt": data.get("totSellamnt"),
                "firstAccumamnt": data.get("firstAccumamnt"),
                "firstPrzwnerCo": data.get("firstPrzwnerCo"),
                "firstWinamnt": data.get("firstWinamnt")
            }
    except Exception:
        # 응답이 깨지거나 HTML 에러 페이지일 경우 무시하고 종료
        pass
    return None

def update_lotto_csv():
    """기존 CSV 파일을 확인하고 누락된 최신 회차 데이터를 자동 수집하여 업데이트"""
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        last_drw = int(df['drwNo'].max()) if 'drwNo' in df.columns and not df.empty else 0
    else:
        df = pd.DataFrame()
        last_drw = 0
    
    print(f"현재 저장된 마지막 로또 회차: {last_drw}회")
    
    current_drw = last_drw + 1
    new_rows = []
    
    while True:
        print(f"{current_drw}회차 데이터 확인 중...")
        data = get_lotto_data(current_drw)
        if not data:
            print(f"아직 추첨되지 않았거나 최신 회차에 도달했습니다 ({current_drw}회).")
            break
        new_rows.append(data)
        print(f"-> 성공적으로 불러옴: {current_drw}회차 ({data['drwNoDate']})")
        current_drw += 1
        
    if new_rows:
        new_df = pd.DataFrame(new_rows)
        if not df.empty:
            df = pd.concat([df, new_df], ignore_index=True)
        else:
            df = new_df
        df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
        print(f"✨ 총 {len(new_rows)}개 회차가 성공적으로 업데이트되었습니다! 최신 회차: {current_drw - 1}회")
    else:
        print("✅ 이미 최신 데이터까지 모두 업데이트되어 있습니다.")

if __name__ == "__main__":
    update_lotto_csv()