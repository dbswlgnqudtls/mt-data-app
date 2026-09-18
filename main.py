import requests
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  # 파이썬 기본 내장 모듈. 시간대 계산용 (별도 설치 불필요)
 
# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(page_title="어제의 박스오피스", page_icon="🎬", layout="wide")
 
KOBIS_URL = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
 
 
def get_yesterday_kst() -> str:
    """한국 시간(KST) 기준으로 '어제' 날짜를 yyyymmdd 형식 문자열로 돌려준다."""
    now_kst = datetime.now(ZoneInfo("Asia/Seoul"))
    yesterday_kst = now_kst - timedelta(days=1)
    return yesterday_kst.strftime("%Y%m%d")
 
 
# -----------------------------
# API 호출 함수
# -----------------------------
# @st.cache_data(ttl=3600) : 같은 target_dt로 다시 호출하면,
# 1시간(3600초) 동안은 실제 API를 다시 부르지 않고 저장해둔 결과를 그대로 재사용한다.
@st.cache_data(ttl=3600)
def fetch_box_office(target_dt: str) -> dict:
    """KOBIS 일별 박스오피스 API를 호출해서 원본 JSON(dict)을 돌려준다."""
    api_key = st.secrets["KOBIS_KEY"]  # 비밀 금고에서만 불러오고, 코드에는 절대 쓰지 않음
    params = {"key": api_key, "targetDt": target_dt}
    response = requests.get(KOBIS_URL, params=params, timeout=10)
    response.raise_for_status()  # 상태코드가 200이 아니면 여기서 예외 발생
    return response.json()
 
 
# -----------------------------
# 화면 그리기 시작
# -----------------------------
st.title("🎬 어제의 박스오피스")
 
target_dt = get_yesterday_kst()
target_dt_display = f"{target_dt[0:4]}년 {target_dt[4:6]}월 {target_dt[6:8]}일"
st.caption(f"조회 기준일(한국 시간, 어제): {target_dt_display}")
 
# -----------------------------
# API 호출 + 오류 처리
# -----------------------------
data = None
error_message = None
 
try:
    data = fetch_box_office(target_dt)
except requests.exceptions.RequestException:
    # 인터넷 연결 문제, 타임아웃, KOBIS 서버 문제 등 요청 자체가 실패한 경우
    error_message = (
        "박스오피스 정보를 불러오는 데 실패했습니다.\n\n"
        "다음을 확인해 주세요.\n"
        "- 인터넷 연결 상태\n"
        "- KOBIS 서버가 정상 동작 중인지\n"
        "- 잠시 후 다시 시도"
    )
 
# 요청은 성공했지만, 응답 내용에 문제가 있는 경우 확인
if data is not None and error_message is None:
    if "faultInfo" in data:
        # 인증키가 틀렸거나, 잘못된 요청일 때 상태코드는 200이지만 faultInfo가 온다
        fault = data["faultInfo"]
        fault_msg = fault.get("message", "알 수 없는 오류")
        error_message = (
            "KOBIS API에서 오류 응답(faultInfo)을 보냈습니다.\n\n"
            f"오류 메시지: {fault_msg}\n\n"
            "다음을 확인해 주세요.\n"
            "- 스트림릿 Secrets에 등록한 KOBIS_KEY 값이 정확한지\n"
            "- 인증키가 만료되지 않았는지\n"
            "- 요청 날짜(targetDt) 형식이 올바른지"
        )
    else:
        movie_list = (
            data.get("boxOfficeResult", {}).get("dailyBoxOfficeList", [])
        )
        if not movie_list:
            error_message = (
                "영화 목록이 비어 있습니다.\n\n"
                "다음을 확인해 주세요.\n"
                "- 조회 날짜(어제)가 실제로 박스오피스 집계가 있는 날짜인지\n"
                "  (아주 오래된 날짜이거나, 아직 집계 전인 날짜는 비어 있을 수 있습니다)\n"
                "- KOBIS 서버 점검 여부"
            )
 
# -----------------------------
# 오류가 있으면 안내 문구만 보여주고 종료
# -----------------------------
if error_message:
    st.error(error_message)
    st.stop()
 
# -----------------------------
# 정상 데이터 -> 표로 정리
# -----------------------------
movie_list = data["boxOfficeResult"]["dailyBoxOfficeList"]
 
rows = []
for movie in movie_list:
    rows.append(
        {
            "순위": int(movie["rank"]),           # 문자열 -> 숫자로 변환 (정렬/계산용)
            "영화명": movie["movieNm"],
            "개봉일": movie["openDt"],
            "관객수": int(movie["audiCnt"]),
            "누적관객": int(movie["audiAcc"]),
            "스크린수": int(movie["scrnCnt"]),
        }
    )
 
df = pd.DataFrame(rows).sort_values("순위").reset_index(drop=True)
 
# -----------------------------
# 1위 영화 지표 카드 3장
# -----------------------------
top_movie = df.iloc[0]
 
st.subheader(f"🥇 1위: {top_movie['영화명']}")
col1, col2, col3 = st.columns(3)
col1.metric("어제 관객수", f"{top_movie['관객수']:,} 명")
col2.metric("누적 관객수", f"{top_movie['누적관객']:,} 명")
col3.metric("스크린수", f"{top_movie['스크린수']:,} 개")
 
st.divider()
 
# -----------------------------
# 전체 순위 표
# -----------------------------
st.subheader("📋 전체 순위")
st.dataframe(
    df.style.format({"관객수": "{:,}", "누적관객": "{:,}", "스크린수": "{:,}"}),
    use_container_width=True,
    hide_index=True,
)
 
st.divider()
 
# -----------------------------
# 관객수 상위 5편 막대그래프
# -----------------------------
st.subheader("📊 관객수 상위 5편")
top5 = df.sort_values("관객수", ascending=False).head(5).set_index("영화명")
st.bar_chart(top5["관객수"])
