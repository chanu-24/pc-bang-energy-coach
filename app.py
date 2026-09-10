# app.py
import streamlit as st
import pandas as pd
import chromadb

st.set_page_config(
    page_title="PC방 AI 에너지 코치",
    page_icon="⚡",
    layout="centered"
)

# 1. 백엔드: 설비별 정격 스펙 및 상세 계산 파이프라인
@st.cache_data
def load_pc_bang_data():
    equipment_df = pd.DataFrame([
        {"equipment": "PC_MONITOR", "name": "💻 PC 및 모니터 (대기전력 관리)", "rated_power_kw": 0.25, "default_hours": 24},
        {"equipment": "HVAC", "name": "❄️ 냉방 및 환기 설비 (에어컨/공조)", "rated_power_kw": 3.5, "default_hours": 10},
        {"equipment": "KITCHEN", "name": "🧊 냉장고 및 주방 가전 (쇼케이스/조리기구)", "rated_power_kw": 2.0, "default_hours": 12}
    ])
    return equipment_df

def calculate_detailed_impact(answers, equipment_df):
    CARBON_FACTOR = 0.4781
    KRW_PER_KWH = 130.0 
    
    pc_count = answers.get("pc_count", 100)
    op_hours = answers.get("op_hours", 24)
    ac_count = answers.get("ac_count", 4)
    ac_hours = answers.get("ac_hours", 10)
    
    before_results = []
    after_results = []
    
    for _, row in equipment_df.iterrows():
        eq = row["equipment"]
        
        if eq == "PC_MONITOR":
            # 기존 소비량
            idle_map = {"0%": 1.0, "1~10%": 1.05, "11~30%": 1.15, "31~50%": 1.3, "51% 이상": 1.4, "모름": 1.1}
            idle_w = idle_map.get(answers.get("q3_idle", "1~10%"), 1.1)
            manage_map = {"자동 절전": 0.9, "자동 종료": 0.9, "직접 종료": 1.0, "모니터만 끔": 1.2, "둘 다 켜둠": 1.4, "모름": 1.1}
            manage_w = manage_map.get(answers.get("q4_pc_manage", "직접 종료"), 1.1)
            
            b_kwh = row["rated_power_kw"] * pc_count * op_hours * 30 * (idle_w * manage_w * 0.45)
            # 개선 후 (최적화 시 대기전력 차단 및 빈 좌석 효율화로 약 25% 절감)
            a_kwh = b_kwh * 0.75
            
        elif eq == "HVAC":
            temp_map = {"22℃ 이하": 1.3, "23~24℃": 1.1, "25℃": 1.0, "26℃ 이상": 0.9, "모름": 1.1, "미사용": 0.0}
            temp_w = temp_map.get(answers.get("q9_temp", "25℃"), 1.0)
            door_map = {"출입할 때만 열고 닫음": 0.9, "자주 열려있음": 1.2, "계속 열어둠": 1.4, "모름": 1.1, "미사용": 1.0}
            door_w = door_map.get(answers.get("q12_door", "출입할 때만 열고 닫음"), 1.0)
            
            b_kwh = row["rated_power_kw"] * ac_count * ac_hours * 30 * temp_w * door_w
            # 개선 후 (적정 온도 26도 유지 및 문 여닫기 개선으로 약 20% 절감)
            a_kwh = b_kwh * 0.80
            
        else: # 냉장고 및 주방 가전
            b_kwh = row["rated_power_kw"] * 2 * 24 * 30 * 1.1
            # 개선 후 (야간 커튼 및 절전 모드 적용으로 약 15% 절감)
            a_kwh = b_kwh * 0.85

        # 비용 및 탄소 환산
        b_cost = b_kwh * KRW_PER_KWH
        a_cost = a_kwh * KRW_PER_KWH
        
        b_carbon = b_kwh * CARBON_FACTOR
        a_carbon = a_kwh * CARBON_FACTOR
        
        before_results.append({"equipment": eq, "name": row["name"], "kwh": round(b_kwh, 1), "cost": round(b_cost), "carbon": round(b_carbon, 1)})
        after_results.append({"equipment": eq, "name": row["name"], "kwh": round(a_kwh, 1), "cost": round(a_cost), "carbon": round(a_carbon, 1)})
        
    return pd.DataFrame(before_results), pd.DataFrame(after_results)

# 2. 백엔드: Python Rule Engine
def python_rule_engine(answers):
    diagnoses = []
    if answers.get("q4_pc_manage") in ["모니터만 끔", "둘 다 켜둠"]:
        diagnoses.append({
            "title": "손님 없는 빈 좌석의 PC·모니터 전원 방치",
            "description": "빈 좌석에서 본체와 모니터 전원이 계속 켜져 있어 불필요한 대기전력이 소모되고 있습니다.",
            "equipment": "PC_MONITOR", "risk_score": 90
        })
    if answers.get("q9_temp") in ["22℃ 이하", "23~24℃"]:
        diagnoses.append({
            "title": "에어컨 설정 온도 과도 저온 유지",
            "description": "실내 적정 온도(26℃)보다 낮게 설정되어 냉방 전력이 과다하게 소모되고 있습니다.",
            "equipment": "HVAC", "risk_score": 85
        })
    if answers.get("q12_door") in ["자주 열려있음", "계속 열어둠"]:
        diagnoses.append({
            "title": "냉방 중 출입문 개방으로 인한 냉기 손실",
            "description": "출입문이 열려 있어 냉기가 지속 유실되며 냉방 에어컨 부하가 가중되고 있습니다.",
            "equipment": "HVAC", "risk_score": 80
        })
    if not diagnoses:
        diagnoses.append({
            "title": "전반적인 매장 설비 대기전력 점검",
            "description": "현재 양호하나 미세 전력 누수를 정기적으로 점검하는 것을 권장합니다.",
            "equipment": "PC_MONITOR", "risk_score": 40
        })
    return sorted(diagnoses, key=lambda x: x["risk_score"], reverse=True)

# 3. 백엔드: ChromaDB RAG
@st.cache_resource
def init_rag_db():
    client = chromadb.Client()
    col = client.get_or_create_collection(name="pc_bang_energy_guide")
    if col.count() == 0:
        col.add(ids=["doc_1"], documents=["[에너지공단] PC·모니터 절전: 빈 좌석 자동 타임아웃 및 마스터 차단기로 대기전력 원천 차단."], metadatas=[{"equipment": "PC_MONITOR"}])
        col.add(ids=["doc_2"], documents=["[에너지공단] 냉방 효율화: 에어컨 설정온도 26도 유지 및 문 닫고 냉방하기로 전력 손실 방지."], metadatas=[{"equipment": "HVAC"}])
        col.add(ids=["doc_3"], documents=["[에너지공단] 냉장고 및 주방가전: 야간 단열 커튼 설치 및 불필요한 예열 차단."], metadatas=[{"equipment": "KITCHEN"}])
    return col

rag_collection = init_rag_db()

def search_rag_guides(eq):
    results = rag_collection.query(query_texts=["에너지 절감 가이드"], n_results=1, where={"equipment": eq})
    return results["documents"][0][0] if results["documents"] else "관련 공식 가이드가 없습니다."

# 4. 세션 상태 초기화
if "step" not in st.session_state:
    st.session_state.step = 1
if "answers" not in st.session_state:
    st.session_state.answers = {
        "pc_count": 100, "op_hours": 24, "ac_count": 4, "ac_hours": 10,
        "q3_idle": "1~10%", "q4_pc_manage": "직접 종료", "q9_temp": "25℃", "q12_door": "출입할 때만 열고 닫음"
    }

# [페이지 1] 15문항 상세 설문
if st.session_state.step == 1:
    st.title("⚡ PC방 에너지 진단 설문 (15개 문항)")
    st.write("매장 운영 상태를 입력하시면 맞춤형 전력 분석이 시작됩니다.")
    
    with st.form("survey_form"):
        st.subheader("1 매장 운영과 빈 좌석 관리")
        pc_count = st.number_input("1. PC방 좌석은 총 몇 석인가요?", min_value=10, max_value=500, value=st.session_state.answers.get("pc_count", 100), step=10)
        op_hours = st.slider("2. 하루에 몇 시간 영업하시나요?", min_value=1, max_value=24, value=st.session_state.answers.get("op_hours", 24))
        q3_idle = st.radio("3. 영업시간 전체 평균 빈 좌석 비율은?", ["0%", "1~10%", "11~30%", "31~50%", "51% 이상", "모름"])
        q4_pc_manage = st.radio("4. 손님 없는 좌석 PC·모니터 관리 방식은?", ["자동 절전", "자동 종료", "직접 종료", "모니터만 끔", "둘 다 켜둠", "모름"])
        
        st.subheader("2 장비 정보와 냉방 관리")
        ac_count = st.number_input("8. 설치된 에어컨 대수", min_value=0, max_value=30, value=st.session_state.answers.get("ac_count", 4))
        q9_temp = st.radio("9. 여름철 에어컨 설정 온도", ["22℃ 이하", "23~24℃", "25℃", "26℃ 이상", "모름", "미사용"])
        ac_hours = st.slider("10. 하루 평균 냉방 사용 시간", min_value=0, max_value=24, value=st.session_state.answers.get("ac_hours", 10))
        
        st.subheader("3 냉방 습관 및 출입문 관리")
        q12_door = st.radio("12. 냉방 중 출입문 관리 방식", ["출입할 때만 열고 닫음", "자주 열려있음", "계속 열어둠", "모름", "미사용"])

        submitted = st.form_submit_button("AI 정밀 진단하기 🚀", use_container_width=True)
        if submitted:
            st.session_state.answers = {
                "pc_count": pc_count, "op_hours": op_hours,
                "q3_idle": q3_idle, "q4_pc_manage": q4_pc_manage,
                "ac_count": ac_count, "q9_temp": q9_temp,
                "ac_hours": ac_hours, "q12_door": q12_door
            }
            st.session_state.step = 2
            st.rerun()

# [페이지 2] 진단 결과
elif st.session_state.step == 2:
    st.title("🔍 AI 에너지 진단 결과")
    diagnoses = python_rule_engine(st.session_state.answers)
    
    avg_risk = sum([d["risk_score"] for d in diagnoses]) / len(diagnoses)
    efficiency_score = max(30, int(100 - (avg_risk * 0.7)))
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric(label="종합 에너지 효율 점수", value=f"{efficiency_score}점", delta="개선 필요" if efficiency_score < 80 else "우수함")
    with col2:
        st.info(f"💡 입력하신 **{st.session_state.answers.get('pc_count')}석** 매장의 핵심 낭비 요인을 진단했습니다.")
        
    st.subheader("🚨 우선 개선 영역 및 RAG 가이드")
    for diag in diagnoses:
        guide = search_rag_guides(diag["equipment"])
        st.markdown(f"""
        <div style="background-color:#f8fafc; border:1px solid #e2e8f0; padding:15px; border-radius:10px; margin-bottom:10px;">
            <h4>{diag['title']} <span style="color:#ef4444; font-size:12px;">[위험점수: {diag['risk_score']}]</span></h4>
            <p style="color:#475569; margin:5px 0;">{diag['description']}</p>
            <hr style="margin:8px 0; border:0; border-top:1px solid #cbd5e1;">
            <p style="font-size:13px; color:#047857; margin:0;"><b>📘 에너지공단 가이드:</b> {guide}</p>
        </div>
        """, unsafe_allow_html=True)
        
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⬅️ 설문 수정하기", use_container_width=True):
            st.session_state.step = 1; st.rerun()
    with c2:
        if st.button("📈 상세 감액 분석 보기 ➔", use_container_width=True):
            st.session_state.step = 3; st.rerun()

# [페이지 3] 상세 감액 비교 분석 (요청하신 디테일 반영)
elif st.session_state.step == 3:
    pc_count_val = st.session_state.answers.get("pc_count", 100)
    st.title(f"📈 항목별 전력 및 요금 감액 상세 분석 ({pc_count_val}석 기준)")
    st.write("개선 전후의 구체적인 전력량 및 요금 변화를 설비별로 확인하실 수 있습니다.")
    
    eq_df = load_pc_bang_data()
    b_df, a_df = calculate_detailed_impact(st.session_state.answers, eq_df)
    
    tot_b_kwh, tot_a_kwh = b_df["kwh"].sum(), a_df["kwh"].sum()
    tot_b_cost, tot_a_cost = b_df["cost"].sum(), a_df["cost"].sum()
    tot_b_carb, tot_a_carb = b_df["carbon"].sum(), a_df["carbon"].sum()
    
    # 상단 요약 카드 (텍스트 생략 없이 깔끔하게 표시)
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("월 총 전력 사용량", f"{int(tot_a_kwh):,} kWh", f"↓ {int(tot_b_kwh - tot_a_kwh):,} 절감 (기존 {int(tot_b_kwh):,})")
    with m2:
        st.metric("월 총 전기요금", f"{int(tot_a_cost):,} 원", f"↓ {int(tot_b_cost - tot_a_cost):,}원 감액")
    with m3:
        st.metric("월 탄소 배출량", f"{round(tot_a_carb, 1)} kg", f"↓ {round(tot_b_carb - tot_a_carb, 1)} kg 감축")
        
    st.markdown("---")
    st.subheader("🔍 설비별 상세 전력 및 요금 감액 내역")
    
    # 설비별 디테일 카드 출력 (요청하신 "몇 kWh에서 몇 kWh로, 얼마에서 얼마가 줄었다" 형식 구현)
    for i in range(len(b_df)):
        name = b_df.loc[i, "name"]
        b_kwh, a_kwh = b_df.loc[i, "kwh"], a_df.loc[i, "kwh"]
        b_cost, a_cost = b_df.loc[i, "cost"], a_df.loc[i, "cost"]
        diff_kwh = round(b_kwh - a_kwh, 1)
        diff_cost = int(b_cost - a_cost)
        
        st.markdown(f"""
        <div style="background-color:#f1f5f9; border-left:5px solid #3b82f6; padding:15px; border-radius:8px; margin-bottom:12px;">
            <h4 style="margin:0 0 8px 0; color:#1e293b;">{name}</h4>
            <p style="margin:4px 0; font-size:14px; color:#334155;">
               • <b>전력량 변화:</b> <span style="color:#dc2626;">{b_kwh:,.1f} kWh</span> ➔ <span style="color:#16a34a;">{a_kwh:,.1f} kWh</span> (<b>총 {diff_kwh:,.1f} kWh 절감</b>)
            </p>
            <p style="margin:4px 0; font-size:14px; color:#334155;">
               • <b>요금 변화:</b> <span style="color:#dc2626;">{b_cost:,} 원</span> ➔ <span style="color:#16a34a;">{a_cost:,} 원</span> (<b>총 {diff_cost:,} 원 감액</b>)
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📊 설비별 비교 요약 테이블")
    comparison_df = pd.DataFrame({
        "설비 부문": b_df["name"],
        "기존 전력": b_df["kwh"].apply(lambda x: f"{x:,.1f} kWh"),
        "개선 후 전력": a_df["kwh"].apply(lambda x: f"{x:,.1f} kWh"),
        "기존 요금": b_df["cost"].apply(lambda x: f"{x:,} 원"),
        "개선 후 요금": a_df["cost"].apply(lambda x: f"{x:,} 원"),
        "월 감액 금액": (b_df["cost"] - a_df["cost"]).apply(lambda x: f"{int(x):,} 원")
    })
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
    if st.button("🔄 처음으로 돌아가기", use_container_width=True):
        st.session_state.step = 1
        st.rerun()