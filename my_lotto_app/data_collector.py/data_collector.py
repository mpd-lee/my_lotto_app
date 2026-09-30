import pandas as pd

# 최근 회차(1100~1104회) 데이터를 직접 입력하여 CSV 파일 생성
data = [
    {"drwNo": 1100, "drwNoDate": "2023-12-30", "drwtNo1": 17, "drwtNo2": 26, "drwtNo3": 29, "drwtNo4": 30, "drwtNo5": 31, "drwtNo6": 43, "bnusNo": 12},
    {"drwNo": 1101, "drwNoDate": "2024-01-06", "drwtNo1": 6, "drwtNo2": 7, "drwtNo3": 13, "drwtNo4": 28, "drwtNo5": 36, "drwtNo6": 42, "bnusNo": 41},
    {"drwNo": 1102, "drwNoDate": "2024-01-13", "drwtNo1": 13, "drwtNo2": 14, "drwtNo3": 22, "drwtNo4": 26, "drwtNo5": 37, "drwtNo6": 38, "bnusNo": 20},
    {"drwNo": 1103, "drwNoDate": "2024-01-20", "drwtNo1": 10, "drwtNo2": 12, "drwtNo3": 29, "drwtNo4": 31, "drwtNo5": 40, "drwtNo6": 44, "bnusNo": 2},
    {"drwNo": 1104, "drwNoDate": "2024-01-27", "drwtNo1": 1, "drwtNo2": 7, "drwtNo3": 21, "drwtNo4": 30, "drwtNo5": 35, "drwtNo6": 38, "bnusNo": 2}
]

df = pd.DataFrame(data)
df.to_csv("lotto_data.csv", index=False, encoding="utf-8-sig")
print("✅ 임시 lotto_data.csv 파일이 성공적으로 생성되었습니다! 이제 다음 단계로 넘어갑시다.")