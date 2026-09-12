# app.py
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="PC방 스마트 에너지 코치",
    page_icon="⚡",
    layout="centered"
)

# PC방 스타일 모던 다크/라이트 CSS 적용
st.markdown("""
    <style>
    .main-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 15px;
    }
    .metric-box {
        background-color: #1e293b;
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if "step" not in st.session_state:
    st.session_state.step = 1
if "answers" not in st.session_state:
    st.session_state.answers = {"pc_count": 50}

# [화면 1] 기본 정보 입력 및 모니터 영역 (질문 3개)
if st.session_state.step == 1:
    st.title("⚡ PC방 스마트 에너지 코치")
    st.caption("전기를 아껴 인건비를 건지는 스마트 매장 솔루션")
    
    st.markdown("### 🖥️ 1단계: 모니터 영역 점검")
    pc_count = st.number_input("매장 총 PC 및 모니터 대수", min_value=10, max_value=300, value=st.session_state.answers.get("pc_count", 50), step=10)
    
    m1 = st.selectbox("1. 손님이 없는 빈 좌석에서도 모니터 전원 및 대기 상태가 그대로 방치되나요?", ["전혀 관리 안 함", "부분 관리", "자동 절전 시스템 완비"])
    m2 = st.selectbox("2. 모니터 응답 속도 및 주사율(Hz)을 고정하여 불필요한 전력 소모를 막고 계신가요?", ["기본 설정 그대로", "일부 타협", "최적화 설정 적용"])
    m3 = st.selectbox("3. 모니터 주변 기기(스탠드 조명, 허브 등) 전력 차단 멀티탭을 사용하시나요?", ["상시 켜둠", "수동 소등", "자동 차단 멀티탭 사용"])
    
    if st.button("다음: 설비/본체 영역으로 ➔", use_container_width=True):
        st.session_state.answers["pc_count"] = pc_count
        st.session_state.answers["monitor"] = [m1, m2, m3]
        st.session_state.step = 2
        st.rerun()

# [화면 2] 설비 및 본체 영역 (질문 3개)
elif st.session_state.step == 2:
    st.title("⚡ PC방 스마트 에너지 코치")
    st.markdown("### 💻 2단계: 설비 및 본체(프레임/업데이트) 영역")
    
    h1 = st.selectbox("1. 게임 최대 프레임 수 제한(백그라운드/메뉴 포함)을 설정하여 GPU 과열을 막고 계신가요?", ["제한 없음", "일부 게임만 제한", "매장 전체 공통 제한"])
    h2 = st.selectbox("2. 야간 게임 업데이트 대기 시 빈 PC를 미리 켜두고 대기전력을 낭비하시나요?", ["업데이트 몇 시간 전부터 켜둠", "시작 전 잠시 켜둠", "Wake-on-LAN 원격 제어 활용"])
    h3 = st.selectbox("3. 업데이트가 완료된 빈 좌석 PC를 곧바로 자동 절전/종료 처리하시나요?", ["다음 손님 올 때까지 방치", "직원이 뒤늦게 수동 종료", "완료 즉시 자동 절전"])
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 이전", use_container_width=True):
            st.session_state.step = 1; st.rerun()
    with col2:
        if st.button("다음: 주방 영역으로 ➔", use_container_width=True):
            st.session_state.answers["hardware"] = [h1, h2, h3]
            st.session_state.step = 3
            st.rerun()

# [화면 3] 주방 영역 (질문 3개)
elif st.session_state.step == 3:
    st.title("⚡ PC방 스마트 에너지 코치")
    st.markdown("### 🍳 3단계: 주방 가전 영역")
    
    k1 = st.selectbox("1. 온수기, 제빙기, 전자레인지 등 주방 가전의 대기전력 및 상시 가동을 관리하시나요?", ["24시간 상시 켜둠", "부분 절전", "시간대별 타이머/스마트 멀티탭 제어"])
    k2 = st.selectbox("2. 손님이 적은 심야 시간에 주방 조리대 및 보조 가전 전원을 분리 소등하시나요?", ["전체 켜둠", "일부만 소등", "구역별 완벽 분리 소등"])
    k3 = st.selectbox("3. 냉장/냉동 쇼케이스 문 개폐 및 온도 설정을 에너지 절약형으로 운영하시나요?", ["기본 설정", "수시 점검", "최적 온도 및 효율 관리"])
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 이전", use_container_width=True):
            st.session_state.step = 2; st.rerun()
    with col2:
        if st.button("다음: 조명 및 냉난방 영역으로 ➔", use_container_width=True):
            st.session_state.answers["kitchen"] = [k1, k2, k3]
            st.session_state.step = 4
            st.rerun()

# [화면 4] 조명 및 냉난방 영역 (질문 3개)
elif st.session_state.step == 4:
    st.title("⚡ PC방 스마트 에너지 코치")
    st.markdown("### 💡❄️ 4단계: 조명 및 냉난방 영역")
    
    l1 = st.selectbox("1. 손님이 적은 시간대에 매장 전체를 밝히지 않고 특정 구역(존)으로만 안내하시나요?", ["매장 전체 자유 이용", "일부 구역 제한 운영", "저이용 구역 소등 및 집중 안내"])
    l2 = st.selectbox("2. 키보드·마우스·헤드셋 거치대 등 게이밍 주변기기 조명 대기전력을 관리하시나요?", ["상시 점등", "일부 소등", "미사용 시 자동 소등/밝기 조절"])
    l3 = st.selectbox("3. 냉난방기와 홀 조명을 구역별로 독립 제어하여 낭비를 줄이고 계신가요?", ["통합 제어/상시 가동", "수동 조절", "구역별 스마트 독립 제어"])
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 이전", use_container_width=True):
            st.session_state.step = 3; st.rerun()
    with col2:
        if st.button("🚀 AI 진단 및 절감액 확인하기", use_container_width=True):
            st.session_state.answers["lighting"] = [l1, l2, l3]
            st.session_state.step = 5
            st.rerun()

# [화면 5] 주의 화면 및 상세 절감액 / 인건비 환산 결과
elif st.session_state.step == 5:
    st.title("📊 매장 에너지 진단 & 인건비 환산 리포트")
    
    pc_count = st.session_state.answers.get("pc_count", 50)
    
    # 가상의 시뮬레이션 계산 (모니터, 설비, 주방, 조명 영역별 세분화)
    # 전기요금 단가: 1kWh당 130원, 최저시급 등 인건비 환산 (시간당 약 10,030원 기준 월 환산)
    base_kwh = pc_count * 180  # 월 기준 기본 전력 사용량 가정
    saved_kwh = int(base_kwh * 0.35) # 약 35% 절감 가능 가정
    base_cost = base_kwh * 130
    saved_cost = saved_kwh * 130
    
    # 인건비 환산 (절약된 금액으로 알바생 몇 시간 또는 월 몇 시간 더 고용할 수 있는지 환산)
    hourly_wage = 10030
    saved_hours = int(saved_cost / hourly_wage)
    
    st.markdown(f"""
    <div style="background-color:#1e293b; color:white; padding:20px; border-radius:12px; margin-bottom:20px;">
        <h3 style="margin:0; color:#38bdf8;">💡 아낀 전기요금이 곧 알바생 인건비!</h3>
        <p style="font-size:16px; margin-top:10px;">
            현재 매장 운영 방식을 개선하면, 월 <b>{saved_cost:,} 원</b>의 전기요금을 아낄 수 있습니다.<br>
            이는 알바생을 약 <b>{saved_hours}시간</b> 더 고용할 수 있는 엄청난 금액입니다!
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 총괄 지표 비교
    col1, col2 = st.columns(2)
    with col1:
        st.metric("월 총 전력 사용량", f"{base_kwh:,} kWh", f"↓ {saved_kwh:,} kWh 감소", delta_color="inverse")
    with col2:
        st.metric("월 총 전기요금", f"{base_cost:,} 원", f"↓ {saved_cost:,} 원 절감", delta_color="inverse")
        
    st.markdown("---")
    st.subheader("🔍 영역별 상세 전력 감소 및 인건비 환산 효과")
    
    # 영역별 비중 배분 (모니터 30%, 설비/본체 30%, 주방 20%, 조명/냉난방 20%)
    areas = [
        {"name": "🖥️ 모니터 영역", "share": 0.30, "tip": "빈 좌석 자동 절전 및 주사율 최적화"},
        {"name": "💻 설비/본체 영역", "share": 0.30, "tip": "프레임 제한 및 업뎃 전후 대기전력 차단"},
        {"name": "🍳 주방 가전 영역", "share": 0.20, "tip": "온수기/제빙기 타이머 제어 및 심야 소등"},
        {"name": "💡 조명/냉난방 영역", "share": 0.20, "tip": "저이용 시간 구역 집중화 및 주변기기 조명 끄기"}
    ]
    
    for area in areas:
        a_kwh = int(saved_kwh * area["share"])
        a_cost = int(saved_cost * area["share"])
        a_hours = int(a_cost / hourly_wage)
        
        st.markdown(f"""
        <div class="main-card">
            <h4 style="margin:0 0 8px 0; color:#0f172a;">{area['name']}</h4>
            <p style="margin:4px 0; font-size:14px; color:#475569;">
               • <b>예상 전력 감소:</b> 약 <b>{a_kwh:,} kWh</b> 절감<br>
               • <b>요금 감액 효과:</b> 약 <b>{a_cost:,} 원</b> 절약 (인건비 <b>{a_hours}시간</b>분 확보)<br>
               • <b>핵심 행동요령:</b> {area['tip']}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    st.subheader("🌱 환경 탄소 감축 효과")
    st.info(f"🌿 본 매장의 에너지 절감으로 월 **{round(saved_kwh * 0.4781, 1)} kg**의 탄소 배출량을 줄여 친환경 PC방 인증에 기여할 수 있습니다.")
    
    if st.button("🔄 처음으로 돌아가기", use_container_width=True):
        st.session_state.step = 1
        st.rerun()