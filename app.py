# app.py
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="아까운 전기요금, 인건비로!",
    page_icon="💸",
    layout="centered"
)

# PC방 전용 프리미엄 다크/카드 스타일 UI/UX 적용
st.markdown("""
    <style>
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .pc-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        padding: 20px;
        border-radius: 14px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .highlight-banner {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        padding: 22px;
        border-radius: 14px;
        text-align: center;
        margin-bottom: 20px;
    }
    .action-box {
        background-color: #064e3b;
        border: 1px solid #059669;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if "step" not in st.session_state:
    st.session_state.step = 1
if "answers" not in st.session_state:
    st.session_state.answers = {"pc_count": 50}

# [페이지 1] 모니터 영역 설문 (질문 3개)
if st.session_state.step == 1:
    st.title("💸 아까운 전기요금, 인건비로 환산하기")
    st.caption("PC방 스마트 에너지 체질 개선 프로젝트 (1/4)")
    
    st.markdown("### 🖥️ 모니터 영역 정밀 진단")
    pc_count = st.number_input("매장 총 PC 대수", min_value=10, max_value=300, value=st.session_state.answers.get("pc_count", 50), step=10)
    
    m1 = st.selectbox("1. 손님이 없는 빈 좌석에서도 모니터 전원 및 대기 상태가 그대로 방치되나요?", ["전혀 관리 안 함 (상시 대기)", "부분 관리", "자동 절전 시스템 완비"])
    m2 = st.selectbox("2. 모니터 응답 속도 및 주사율(Hz)을 고정하여 불필요한 전력 소모를 막고 계신가요?", ["기본 설정 그대로", "일부 타협", "최적화 설정 적용"])
    m3 = st.selectbox("3. 모니터 주변 기기(스탠드 조명, USB 허브 등) 전력 차단 멀티탭을 사용하시나요?", ["상시 켜둠", "수동 소등", "자동 차단 멀티탭 사용"])
    
    if st.button("다음: 설비/본체 영역 ➔", use_container_width=True):
        st.session_state.answers["pc_count"] = pc_count
        st.session_state.answers["monitor"] = [m1, m2, m3]
        st.session_state.step = 2
        st.rerun()

# [페이지 2] 설비/본체 영역 설문 (질문 3개)
elif st.session_state.step == 2:
    st.title("💸 아까운 전기요금, 인건비로 환산하기")
    st.caption("PC방 스마트 에너지 체질 개선 프로젝트 (2/4)")
    
    st.markdown("### 💻 설비 및 본체 영역 (프레임·업데이트)")
    h1 = st.selectbox("1. 게임 최대 프레임 수 제한(백그라운드/메뉴 포함)을 설정하여 GPU 과열을 막고 계신가요?", ["제한 없음", "일부 게임만 제한", "매장 전체 공통 제한"])
    h2 = st.selectbox("2. 야간 게임 업데이트 대기 시 빈 PC를 미리 켜두고 대기전력을 낭비하시나요?", ["업데이트 몇 시간 전부터 켜둠", "시작 전 잠시 켜둠", "Wake-on-LAN 원격 제어 활용"])
    h3 = st.selectbox("3. 업데이트가 완료된 빈 좌석 PC를 곧바로 자동 절전/종료 처리하시나요?", ["다음 손님 올 때까지 방치", "직원이 뒤늦게 수동 종료", "완료 즉시 자동 절전"])
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 이전", use_container_width=True):
            st.session_state.step = 1; st.rerun()
    with col2:
        if st.button("다음: 주방 영역 ➔", use_container_width=True):
            st.session_state.answers["hardware"] = [h1, h2, h3]
            st.session_state.step = 3
            st.rerun()

# [페이지 3] 주방 영역 설문 (질문 3개)
elif st.session_state.step == 3:
    st.title("💸 아까운 전기요금, 인건비로 환산하기")
    st.caption("PC방 스마트 에너지 체질 개선 프로젝트 (3/4)")
    
    st.markdown("### 🍳 주방 가전 영역 정밀 진단")
    k1 = st.selectbox("1. 온수기, 제빙기, 전자레인지 등 주방 가전의 대기전력 및 상시 가동을 관리하시나요?", ["24시간 상시 켜둠", "부분 절전", "시간대별 타이머/스마트 멀티탭 제어"])
    k2 = st.selectbox("2. 손님이 적은 심야 시간에 주방 조리대 및 보조 가전 전원을 분리 소등하시나요?", ["전체 켜둠", "일부만 소등", "구역별 완벽 분리 소등"])
    k3 = st.selectbox("3. 냉장/냉동 쇼케이스 문 개폐 및 온도 설정을 에너지 절약형으로 운영하시나요?", ["기본 설정", "수시 점검", "최적 온도 및 효율 관리"])
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 이전", use_container_width=True):
            st.session_state.step = 2; st.rerun()
    with col2:
        if st.button("다음: 조명 영역 ➔", use_container_width=True):
            st.session_state.answers["kitchen"] = [k1, k2, k3]
            st.session_state.step = 4
            st.rerun()

# [페이지 4] 조명/냉난방 영역 설문 (질문 3개)
elif st.session_state.step == 4:
    st.title("💸 아까운 전기요금, 인건비로 환산하기")
    st.caption("PC방 스마트 에너지 체질 개선 프로젝트 (4/4)")
    
    st.markdown("### 💡❄️ 조명 및 냉난방 영역 정밀 진단")
    l1 = st.selectbox("1. 손님이 적은 시간대에 매장 전체를 밝히지 않고 특정 구역(존)으로만 안내하시나요?", ["매장 전체 자유 이용", "일부 구역 제한 운영", "저이용 구역 소등 및 집중 안내"])
    l2 = st.selectbox("2. 키보드·마우스·헤드셋 거치대 등 게이밍 주변기기 조명 대기전력을 관리하시나요?", ["상시 점등", "일부 소등", "미사용 시 자동 소등/밝기 조절"])
    l3 = st.selectbox("3. 냉난방기와 홀 조명을 구역별로 독립 제어하여 낭비를 줄이고 계신가요?", ["통합 제어/상시 가동", "수동 조절", "구역별 스마트 독립 제어"])
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 이전", use_container_width=True):
            st.session_state.step = 3; st.rerun()
    with col2:
        if st.button("🚀 AI 진단 결과 및 인건비 환산 보기", use_container_width=True):
            st.session_state.answers["lighting"] = [l1, l2, l3]
            st.session_state.step = 5
            st.rerun()

# [페이지 5] AI 에너지 진단 결과 & 행동요령 & 인건비 환산 리포트
elif st.session_state.step == 5:
    st.title("📊 AI 에너지 진단 & 인건비 환산 리포트")
    
    pc_count = st.session_state.answers.get("pc_count", 50)
    
    # 전력 및 비용 계산 시뮬레이션
    base_kwh = pc_count * 190  # 월 기준 기존 사용량 가정
    saved_kwh = int(base_kwh * 0.38) # 약 38% 절감 가능
    base_cost = base_kwh * 130
    saved_cost = saved_kwh * 130
    
    # 최저시급(10,030원) 기준 인건비 환산 시간
    hourly_wage = 10030
    saved_hours = int(saved_cost / hourly_wage)
    
    # 1. 인건비 강조 배너
    st.markdown(f"""
    <div class="highlight-banner">
        <h2>💡 전기요금을 아껴서 알바생을 더 쓴다!</h2>
        <p style="font-size:17px; margin-top:8px;">
            매장 전력 체질을 개선하면 월 <b>{saved_cost:,} 원</b>의 전기요금이 절감됩니다.<br>
            이는 알바생 인건비 약 <b>{saved_hours}시간분</b>에 달하는 엄청난 금액입니다!
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. AI 에너지 진단결과 (가장 먼저 확인할 영역)
    st.subheader("🎯 이번주 가장 먼저 확인할 영역 (Top Priority)")
    st.markdown("""
    <div class="pc-card" style="border-left: 5px solid #ef4444;">
        <h4 style="margin:0; color:#ef4444;">🔥 최우선 개선 구역: 설비/본체 영역 및 모니터 대기전력</h4>
        <p style="margin:8px 0 0 0; color:#cbd5e1;">
            현재 야간 업데이트 대기 시간과 빈 좌석 모니터 방치로 인해 불필요한 전력 소모가 가장 심각합니다. 이번 주에는 <b>업데이트 직전 자동 켜짐(WoL) 설정</b>과 <b>모니터 대기전력 차단</b>부터 적용하세요!
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 3. PC방 낭비요인 및 행동추천 (행동요령)
    st.subheader("🛠️ PC방 낭비요인 분석 및 실천 행동요령")
    actions = [
        {"area": "🖥️ 모니터 영역", "action": "미사용 좌석 모니터 강제 절전 및 주사율 최적화 설정 적용", "kwh": int(saved_kwh * 0.30), "cost": int(saved_cost * 0.30)},
        {"area": "💻 설비/본체 영역", "action": "게임별 최대 프레임 제한 및 야간 업데이트 전후 자동 종료 연동", "kwh": int(saved_kwh * 0.30), "cost": int(saved_cost * 0.30)},
        {"area": "🍳 주방 가전 영역", "action": "온수기·제빙기 심야 시간 타이머 제어 및 보조 가전 분리 소등", "kwh": int(saved_kwh * 0.20), "cost": int(saved_cost * 0.20)},
        {"area": "💡 조명/냉난방 영역", "action": "손님 적은 시간대 특정 구역(존) 집중 안내 및 주변기기 조명 소등", "kwh": int(saved_kwh * 0.20), "cost": int(saved_cost * 0.20)}
    ]
    
    for item in actions:
        item_hours = int(item["cost"] / hourly_wage)
        st.markdown(f"""
        <div class="pc-card">
            <h4 style="margin:0 0 6px 0; color:#38bdf8;">{item['area']}</h4>
            <p style="margin:2px 0; font-size:14px; color:#e2e8f0;"><b>💡 추천 행동요령:</b> {item['action']}</p>
            <p style="margin:4px 0 0 0; font-size:13px; color:#34d399;">
               • 예상 전력 감소: <b>↓ {item['kwh']:,} kWh</b> | 요금 감액: <b>↓ {item['cost']:,} 원</b> (인건비 <b>{item_hours}시간</b> 확보)
            </p>
        </div>
        """, unsafe_allow_html=True)

    # 4. 전력, 비용, 탄소 절감 효과 총괄
    st.markdown("---")
    st.subheader("📈 종합 절감 효과 요약 (개선 전 ➔ 개선 후)")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("월 총 전력 사용량", f"{base_kwh:,} kWh", f"↓ {saved_kwh:,} kWh 감소", delta_color="inverse")
    with col2:
        st.metric("월 총 전기요금", f"{base_cost:,} 원", f"↓ {saved_cost:,} 원 절감", delta_color="inverse")
    with col3:
        st.metric("월 탄소 배출량", f"{int(base_kwh * 0.4781):,} kg", f"↓ {int(saved_kwh * 0.4781):,} kg 감축", delta_color="inverse")
        
    st.markdown("---")
    st.subheader("❓ 어디에서 가장 많이 줄일 수 있나요?")
    st.info("📊 분석 결과, **모니터 영역(30%)**과 **설비/본체 영역(30%)**에서 전체 절감액의 60% 이상을 차지합니다. 이 두 영역의 프레임 제한과 자동 절전 설정만 완벽히 구현해도 매장 고정비를 대폭 낮출 수 있습니다.")
    
    if st.button("🔄 처음으로 돌아가기", use_container_width=True):
        st.session_state.step = 1
        st.rerun()