# app.py
import streamlit as st
import pandas as pd
import chromadb

st.set_page_config(
    page_title="PC방 AI 에너지 코치",
    page_icon="⚡",
    layout="centered"
)

# 1. 백엔드: 5대 영역별 데이터 및 정밀 계산 파이프라인 (모니터, 본체, 주변기기 등 영역별 분리)
@st.cache_data
def load_pc_bang_data():
    equipment_df = pd.DataFrame([
        {"equipment": "FRAME", "category": "🎮 게임 프레임 설정", "name": "GPU 및 본체 연전력 최적화", "rated_power_kw": 0.03, "default_hours": 8},
        {"equipment": "UPDATE_BEFORE", "category": "⏳ 업데이트 전 대기", "name": "업데이트 대기 시간 전력 낭비 방지", "rated_power_kw": 0.08, "default_hours": 2},
        {"equipment": "UPDATE_AFTER", "category": "🛑 업데이트 후 방치", "name": "업데이트 완료 후 PC 방치 차단", "rated_power_kw": 0.08, "default_hours": 3},
        {"equipment": "ZONE_OP", "category": "💡❄️ 구역별 좌석 운영", "name": "저이용 시간 조명 및 냉방 독립 제어", "rated_power_kw": 1.0, "default_hours": 6},
        {"equipment": "PERIPHERAL", "category": "⌨️ 게이밍 주변기기 조명", "name": "키보드·마우스·거치대 조명 대기전력", "rated_power_kw": 0.002, "default_hours": 10}
    ])
    return equipment_df

def calculate_detailed_impact(answers, equipment_df):
    CARBON_FACTOR = 0.4781
    KRW_PER_KWH = 130.0 
    pc_count = answers.get("pc_count", 50)
    
    before_results = []
    after_results = []
    
    for _, row in equipment_df.iterrows():
        eq = row["equipment"]
        ans_val = answers.get(eq, "미흡")
        
        # 선택에 따른 감축 계수
        w_map = {"철저히 준수": 0.1, "부분 적용": 0.5, "미흡": 1.0}
        factor = w_map.get(ans_val, 1.0)
        
        b_kwh = row["rated_power_kw"] * pc_count * row["default_hours"] * 30 * factor
        a_kwh = b_kwh * 0.15 # 개선 시 대폭 감소
        
        b_cost = b_kwh * KRW_PER_KWH
        a_cost = a_kwh * KRW_PER_KWH
        b_carbon = b_kwh * CARBON_FACTOR
        a_carbon = a_kwh * CARBON_FACTOR
        
        before_results.append({"equipment": eq, "category": row["category"], "name": row["name"], "kwh": round(b_kwh, 1), "cost": round(b_cost), "carbon": round(b_carbon, 1)})
        after_results.append({"equipment": eq, "category": row["category"], "name": row["name"], "kwh": round(a_kwh, 1), "cost": round(a_cost), "carbon": round(a_carbon, 1)})
        
    return pd.DataFrame(before_results), pd.DataFrame(after_results)

# 2. 세션 상태 관리 (단계별 화면 이동 제어)
if "step" not in st.session_state:
    st.session_state.step = 1
if "answers" not in st.session_state:
    st.session_state.answers = {"pc_count": 50}

# [화면 1] 기본 정보 및 1단계: 게임 프레임 설정
if st.session_state.step == 1:
    st.title("⚡ PC방 에너지 자가진단 (1/5)")
    st.subheader("🎮 2장. 게임 프레임 설정")
    
    pc_count = st.number_input("매장 총 PC 대수", min_value=10, max_value=300, value=st.session_state.answers.get("pc_count", 50), step=10)
    q_frame = st.radio("게임의 최대 프레임 수를 제한하여 GPU/CPU 연산 전력을 아끼고 계신가요?", ["철저히 준수", "부분 적용", "미흡"], index=2)
    
    if st.button("다음 단계로 ➔", use_container_width=True):
        st.session_state.answers["pc_count"] = pc_count
        st.session_state.answers["FRAME"] = q_frame
        st.session_state.step = 2
        st.rerun()

# [화면 2] 2단계: 업데이트 전 대기
elif st.session_state.step == 2:
    st.title("⚡ PC방 에너지 자가진단 (2/5)")
    st.subheader("⏳ 3장. 업데이트 전 대기 관리")
    
    q_up_before = st.radio("게임 업데이트를 기다리는 동안 빈 좌석 PC를 불필요하게 미리 켜두지 않으시나요?", ["철저히 준수", "부분 적용", "미흡"], index=2)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 이전", use_container_width=True):
            st.session_state.step = 1; st.rerun()
    with col2:
        if st.button("다음 단계로 ➔", use_container_width=True):
            st.session_state.answers["UPDATE_BEFORE"] = q_up_before
            st.session_state.step = 3
            st.rerun()

# [화면 3] 3단계: 업데이트 후 방치
elif st.session_state.step == 3:
    st.title("⚡ PC방 에너지 자가진단 (3/5)")
    st.subheader("🛑 4장. 업데이트 후 방치 관리")
    
    q_up_after = st.radio("업데이트가 끝난 빈 좌석 PC를 자동으로 절전/종료하여 방치 전력을 차단하고 계신가요?", ["철저히 준수", "부분 적용", "미흡"], index=2)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 이전", use_container_width=True):
            st.session_state.step = 2; st.rerun()
    with col2:
        if st.button("다음 단계로 ➔", use_container_width=True):
            st.session_state.answers["UPDATE_AFTER"] = q_up_after
            st.session_state.step = 4
            st.rerun()

# [화면 4] 4단계: 저이용 시간 구역별 운영
elif st.session_state.step == 4:
    st.title("⚡ PC방 에너지 자가진단 (4/5)")
    st.subheader("💡❄️ 5장. 손님이 적은 시간의 좌석 및 냉난방 운영")
    
    q_zone = st.radio("손님이 적은 시간대에 특정 구역으로 손님을 모으고, 빈 구역의 조명·냉방을 끄고 계신가요?", ["철저히 준수", "부분 적용", "미흡"], index=2)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 이전", use_container_width=True):
            st.session_state.step = 3; st.rerun()
    with col2:
        if st.button("다음 단계로 ➔", use_container_width=True):
            st.session_state.answers["ZONE_OP"] = q_zone
            st.session_state.step = 5
            st.rerun()

# [화면 5] 5단계: 게이밍 주변기기 조명
elif st.session_state.step == 5:
    st.title("⚡ PC방 에너지 자가진단 (5/5)")
    st.subheader("⌨️ 6장. 게이밍 주변기기 조명 관리")
    
    q_peri = st.radio("미사용 좌석의 키보드·마우스·거치대 조명 대기전력을 관리(소등/밝기 조절)하고 계신가요?", ["철저히 준수", "부분 적용", "미흡"], index=2)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 이전", use_container_width=True):
            st.session_state.step = 4; st.rerun()
    with col2:
        if st.button("AI 종합 진단 및 절감액 확인하기 🚀", use_container_width=True):
            st.session_state.answers["PERIPHERAL"] = q_peri
            st.session_state.step = 6
            st.rerun()

# [화면 6] 주의 화면 (종합 진단 및 영역별 절감액 분석)
elif st.session_state.step == 6:
    st.title("⚠️ 매장 전력 낭비 주의 화면 (진단 결과)")
    
    eq_df = load_pc_bang_data()
    b_df, a_df = calculate_detailed_impact(st.session_state.answers, eq_df)
    
    tot_b_kwh, tot_a_kwh = b_df["kwh"].sum(), a_df["kwh"].sum()
    tot_b_cost, tot_a_cost = b_df["cost"].sum(), a_df["cost"].sum()
    
    saved_kwh = int(tot_b_kwh - tot_a_kwh)
    saved_cost = int(tot_b_cost - tot_a_cost)
    
    st.error(f"🚨 현재 매장은 총 **{saved_kwh:,} kWh**, 월 **{saved_cost:,} 원**의 전력 요금을 낭비하고 있을 위험이 있습니다!")
    
    st.markdown("---")
    st.subheader("🔍 영역별 상세 절감 및 감소 내역")
    
    for i in range(len(b_df)):
        cat = b_df.loc[i, "category"]
        b_k = b_df.loc[i, "kwh"]
        a_k = a_df.loc[i, "kwh"]
        diff_k = round(b_k - a_k, 1)
        diff_c = int(b_df.loc[i, "cost"] - a_df.loc[i, "cost"])
        
        st.markdown(f"""
        <div style="background-color:#f8fafc; border:1px solid #cbd5e1; padding:12px; border-radius:8px; margin-bottom:10px;">
            <b>{cat}</b><br>
            • 전력 변화: <span style="color:red;">{b_k} kWh</span> ➔ <span style="color:green;">{a_k} kWh</span> (<b>감소량: {diff_k} kWh</b>)<br>
            • 요금 감액: <b>↓ {diff_c:,} 원 절약 가능</b>
        </div>
        """, unsafe_allow_html=True)
        
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 설문 다시하기", use_container_width=True):
            st.session_state.step = 1; st.rerun()
    with col2:
        if st.button("🤖 AI 맞춤 코치 화면 보기 ➔", use_container_width=True):
            st.session_state.step = 7; st.rerun()

# [화면 7] AI 코치 화면
elif st.session_state.step == 7:
    st.title("🤖 AI 에너지 코칭 솔루션")
    st.success("매장 운영 방식을 분석하여 도출된 실시간 맞춤형 코칭 가이드입니다.")
    
    st.markdown("""
    ### 💡 AI 코치의 핵심 개선 제안
    1. **프레임 제한 자동화**: 백그라운드 및 메뉴 화면에서 불필요한 고프레임을 제한하면 하드웨어 수명 연장과 동시에 전력을 즉시 줄일 수 있습니다.
    2. **업데이트 전·후 자동화 연동**: 직원이 일일이 대기하거나 수동으로 끄지 않고, 관리 프로그램의 작업 완료 상태와 연동하여 자동으로 절전 모드로 진입하도록 설정하세요.
    3. **저이용 시간 구역 집중화**: 손님이 적은 야간 시간대에는 특정 구역만 개방하고 나머지 구역의 냉난방 및 일반 조명을 독립 제어하는 것이 가장 효과적입니다.
    """)
    
    if st.button("🔄 처음으로 돌아가기", use_container_width=True):
        st.session_state.step = 1
        st.rerun()