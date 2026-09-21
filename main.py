"""
영화 데이터 그래프 도감 1 - 시간

KOBIS 일별 박스오피스 1년치 데이터를 가지고, '시간'이라는 주제로
그래프를 하나씩 늘려가며 살펴보는 앱입니다.

데이터 출처:
https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_daily.csv
(날짜, 순위, 영화코드, 영화명, 일관객, 누적관객, 스크린수, 상영횟수)
"""

import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(page_title="영화 데이터 그래프 도감 1 - 시간", page_icon="🎞️", layout="wide")

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_daily.csv"


# -----------------------------
# 데이터 불러오기
# -----------------------------
# @st.cache_data : 앱이 다시 실행되어도 매번 인터넷에서 새로 내려받지 않고
# 캐시에 저장된 데이터를 재사용한다. (인터넷 주소의 데이터가 자주 안 바뀌므로
# 기간 제한 없이 캐시해 둔다. 최신 데이터가 필요하면 화면 우측 상단
# 메뉴의 'Clear cache'를 쓰면 된다.)
@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_URL)

    # '날짜' 열은 20250901 같은 여덟 자리 숫자 문자열이다.
    # -> 진짜 날짜(datetime) 타입으로 바꿔서, 날짜순 정렬이나 시계열 그래프에 바로 쓸 수 있게 한다.
    df["날짜"] = pd.to_datetime(df["날짜"], format="%Y%m%d")

    # 숫자로 다뤄야 하는 열들을 혹시 문자열로 들어와도 안전하게 숫자로 바꿔준다.
    # (정렬, 계산, 그래프의 y축에 쓰려면 반드시 숫자 타입이어야 한다.)
    numeric_cols = ["순위", "일관객", "누적관객", "스크린수", "상영횟수"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


df = load_data()

# -----------------------------
# 제목
# -----------------------------
st.title("🎞️ 영화 데이터 그래프 도감 1 - 시간")
st.caption("KOBIS 일별 박스오피스 데이터로, 시간의 흐름에 따른 영화 흥행 변화를 살펴봅니다.")

st.divider()

# =========================================================
# 그래프 구역 1: 영화별 일별 관객수 추이
# =========================================================
st.header("1. 영화별 일별 관객수 추이")

# 드롭다운에 넣을 영화 목록: 관객수가 많은 순으로 정렬해서, 유명한 영화가 위쪽에 오게 한다.
movie_order = (
    df.groupby("영화명")["일관객"].sum().sort_values(ascending=False).index.tolist()
)

selected_movie = st.selectbox("영화를 선택하세요", movie_order)

# 선택한 영화의 데이터만 뽑아서, 날짜순으로 정렬한다.
movie_df = df[df["영화명"] == selected_movie].sort_values("날짜")

fig1 = px.line(
    movie_df,
    x="날짜",
    y="일관객",
    markers=True,
    labels={"날짜": "날짜", "일관객": "일일 관객수"},
    title=f"'{selected_movie}' 일별 관객수 변화",
)
# 마우스를 올렸을 때 날짜와 관객수가 보이도록 hover 형식을 지정한다.
fig1.update_traces(hovertemplate="날짜: %{x|%Y-%m-%d}<br>관객수: %{y:,}명<extra></extra>")
fig1.update_layout(hovermode="x unified")

st.plotly_chart(fig1, use_container_width=True)

# '이 그래프로 알 수 있는 것' 문구를 넣을 자리.
# 나중에 이 자리에 직접 해설 문장을 채워 넣거나, 필요하면 st.text_area를 지우고
# 고정 문구(st.info("..."))로 바꿔도 된다.
st.text_area(
    "📝 이 그래프로 알 수 있는 것",
    placeholder="예: 개봉 직후 관객수가 가장 높았다가, 시간이 지나며 점차 줄어드는 것을 볼 수 있다.",
    key="insight_1",
)

st.divider()

# =========================================================
# 그래프 구역 2: (다음에 추가할 그래프 자리)
# =========================================================
# st.header("2. ...")
# ... 그래프 코드 ...
# st.text_area("📝 이 그래프로 알 수 있는 것", key="insight_2")
# st.divider()

# =========================================================
# 그래프 구역 3: (다음에 추가할 그래프 자리)
# =========================================================
# st.header("3. ...")
