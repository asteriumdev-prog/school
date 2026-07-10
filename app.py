import streamlit as st
import requests
import datetime

# 🔑 나이스 인증키 및 학교 코드 설정
API_KEY = "7d991e334a004a3c8db6f772aa2619fa"
OFFICE_CODE = "B10"      # 서울특별시교육청
SCHOOL_CODE = "7010965"  # 동양고등학교

# 🍴 급식 정보 가져오기
@st.cache_data
def get_dongyang_lunch(target_date):
    url = "https://open.neis.go.kr/hub/mealServiceDietInfo"
    params = {
        "KEY": API_KEY, "Type": "json", 
        "ATPT_OFCDC_SC_CODE": OFFICE_CODE, "SD_SCHUL_CODE": SCHOOL_CODE, "MLSV_YMD": target_date
    }
    try:
        res = requests.get(url, params=params).json()
        if "mealServiceDietInfo" in res:
            lunch_info = res["mealServiceDietInfo"][1]["row"][0]["DDISH_NM"]
            return lunch_info.replace("<br/>", "\n")
        return "등록된 급식 정보가 없습니다. ❌"
    except:
        return "급식 서버 연결 실패 🛠️"

# 📅 학사일정 가져오기
@st.cache_data
def get_dongyang_schedule(target_date):
    url = "https://open.neis.go.kr/hub/SchoolSchedule"
    params = {
        "KEY": API_KEY, "Type": "json", 
        "ATPT_OFCDC_SC_CODE": OFFICE_CODE, "SD_SCHUL_CODE": SCHOOL_CODE, "AA_YMD": target_date
    }
    try:
        res = requests.get(url, params=params).json()
        if "SchoolSchedule" in res:
            events = [row["EVENT_NM"] for row in res["SchoolSchedule"][1]["row"]]
            return ", ".join(events)
        return "특별한 일정이 없습니다. 🏖️"
    except:
        return "일정 서버 연결 실패 🛠️"

# ⏰ 시간표 정보 가져오기 (🚀 중복 제거 및 과목명 통합 기능 적용)
@st.cache_data
def get_dongyang_timetable(target_date, grade, class_nm):
    url = "https://open.neis.go.kr/hub/hisTimetable"
    params = {
        "KEY": API_KEY, 
        "Type": "json", 
        "ATPT_OFCDC_SC_CODE": OFFICE_CODE, 
        "SD_SCHUL_CODE": SCHOOL_CODE, 
        "ALL_TI_YMD": target_date,
        "GRADE": str(grade),
        "CLASS_NM": str(class_nm)
    }
    try:
        res = requests.get(url, params=params).json()
        if "hisTimetable" in res:
            rows = res["hisTimetable"][1]["row"]
            
            # 1. 교시(PERIO)별로 과목들을 모아둡니다.
            timetable_dict = {}
            for row in rows:
                perio = int(row["PERIO"])
                sub = row["ITRT_CNTNT"]
                if perio not in timetable_dict:
                    timetable_dict[perio] = []
                timetable_dict[perio].append(sub)
            
            # 2. 교시별로 중복을 없애고 텍스트를 정리합니다.
            timetable_list = []
            for perio in sorted(timetable_dict.keys()):
                subjects = timetable_dict[perio]
                final_subject = subjects[0] # 기본적으로 겹치는 과목 중 첫 번째만 남김
                
                # 3. 만약 겹치는 과목 중에 과학/문과 키워드가 있으면 이름 통일
                for sub in subjects:
                    if any(k in sub for k in ["물리", "화학", "생명", "지구", "과학"]):
                        final_subject = "과학"
                        break
                    elif any(k in sub for k in ["사회", "지리", "윤리", "역사", "정치", "법", "경제"]):
                        final_subject = "사회"
                        break
                        
                timetable_list.append(f"**{perio}교시**: {final_subject}")
                
            return "\n\n".join(timetable_list)
        return "수업 정보가 없거나 주말/공휴일입니다. 🛌"
    except:
        return "시간표 서버 연결 실패 🛠️"


# ==========================================
# ✨ 스트림릿 웹 화면 구성
# ==========================================

st.set_page_config(page_title="동양고 스마트 알리미", page_icon="🏫", layout="wide")

# ⚙️ 사이드바 컨트롤 패널
with st.sidebar:
    st.header("⚙️ 컨트롤 패널")
    
    now = datetime.datetime.now()
    today_date = now.date()
    selected_date = st.date_input("조회할 날짜를 선택하세요👇", today_date)
    
    st.markdown("---")
    
    st.subheader("👤 학급 선택")
    selected_grade = st.selectbox("학년을 선택하세요", [1, 2, 3], index=1)
    selected_class = st.selectbox("반을 선택하세요", list(range(1, 9)), index=4)

    st.markdown("---")
    st.caption("만든이: 20605")

# 메인 화면 타이틀
st.title("🏫 동양고등학교 스마트 알리미")
st.markdown(f"### 📍 현재 조회 중: **{selected_grade}학년 {selected_class}반**")
st.markdown("---")

# 데이터 가져오기 프로세스
target_date_str = selected_date.strftime("%Y%m%d")
menu = get_dongyang_lunch(target_date_str)
schedule = get_dongyang_schedule(target_date_str)
timetable = get_dongyang_timetable(target_date_str, selected_grade, selected_class)

# 상단 요약 대시보드
csat_date = datetime.date(2026, 11, 19) 
d_day = (csat_date - today_date).days

col1, col2, col3 = st.columns(3)
col1.metric(label="선택된 날짜", value=selected_date.strftime("%m월 %d일"))
col2.metric(label="학사일정 여부", value="일정 있음 🔔" if "없습니다" not in schedule else "일정 없음 🔕")
col3.metric(label="2027학년도 수능", value=f"D-{d_day}" if d_day > 0 else ("D-Day!" if d_day == 0 else "종료"))

st.markdown("---")

# 하단 상세 정보
col_left, col_mid, col_right = st.columns(3)

with col_left:
    st.subheader("📅 상세 학사 일정")
    if "없습니다" in schedule:
        st.info(schedule)
    else:
        st.success(f"**📌 {schedule}**")

with col_mid:
    st.subheader(f"⏰ {selected_grade}-{selected_class} 시간표")
    if "주말" in timetable or "실패" in timetable or "없거나" in timetable:
        st.info(timetable)
    else:
        st.success(timetable)

with col_right:
    st.subheader("🍴 상세 급식 메뉴")
    st.warning(menu)