import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="로또 분석 앱", layout="wide")

st.title("🍀 나만의 로또 당첨 데이터 분석 & 번호 추천기")
st.write("로또 데이터를 확인하고 행운의 번호를 추출해 보는 웹 애플리케이션입니다.")

# 1. 데이터 불러오기
try:
    df = pd.read_csv("lotto_data.csv")
    st.success("✅ 로또 데이터를 성공적으로 불러왔습니다!")
    st.dataframe(df, use_container_width=True)
except FileNotFoundError:
    st.error("⚠️ lotto_data.csv 파일이 없습니다.")

# 2. 행운의 번호 추천 기능
st.markdown("---")
st.subheader("🎲 행운의 반자동/자동 번호 추천")

if st.button("추천 번호 생성하기"):
    lucky_nums = sorted(random.sample(range(1, 46), 6))
    st.balloons()
    st.success(f"🎉 오늘의 추천 행운 번호: **{lucky_nums}**")