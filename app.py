# app.py
import streamlit as st
import pandas as pd
import chromadb

st.set_page_config(
    page_title="PC방 AI 에너지 코치",
    page_icon="⚡",
    layout="centered"
)

# 1. 백엔드: Pandas 데이터 및 계산 파이프라인
@st.cache_data
def load_pc_bang_data():
    equipment_df = pd.DataFrame([
        {"equipment": "PC_MONITOR", "name": "게이밍 PC 및 모니터 전력", "rated_power_kw": 0.25, "default_hours": 24},
        {"equipment": "HVAC", "name": "에어컨 및 환기 설비", "rated_power_kw": 3.5, "default_hours": 10},
        {"equipment": "LIGHTING", "name": "매장 조명 및 기타 설비", "rated_power_kw": 1.0, "default_hours": 12}
    ])
    return equipment_df

def calculate_energy_impact(answers, equipment_df):
    CARBON_FACTOR = 0.4781
    KRW_PER_KWH = 130.0 
    
    pc_count = answers.get("pc_count", 100)
    op_hours = answers.get("op_hours", 24)
    ac_count = answers.get("ac_count", 4)
    ac_hours = answers.get("ac_hours", 10)
    
    results = []
    for _, row in equipment_df.iterrows():
        eq = row["equipment"]
        
        if eq == "PC_MONITOR":
            idle_ratio_map = {"0%": 1.0, "1~10%": 1.05, "11~30%": 1.15, "31~50%": 1.3, "51% 이상": 1.4, "모름": 1.1}
            idle_weight = idle_ratio_map.get(answers.get("q3_idle", "1~10%"), 1.1)
            
            manage_map = {"자동 절전": 0.9, "자동 종료": 0.9, "직접 종료": 1.0, "모니터만 끔": 1.2, "둘 다 켜둠": 1.4, "모름": 1.1}
            manage_weight = manage_map.get(answers.get("q4_pc_manage", "직접 종료"), 1.1)
            
            monthly_kwh = row["rated_power_kw"] * pc_count * op_hours * 30 * (idle_weight * manage_weight * 0.5)
            
        elif eq == "HVAC":
            temp_map = {"22℃ 이하": 1.3, "23~24℃": 1.1, "25℃": 1.0, "26℃ 이상": 0.9, "모름": 1.1, "미사용": 0.0}
            temp_weight = temp_map.get(answers.get("q9_temp", "25℃"), 1.0)
            
            monthly_kwh = row["rated_power_kw"] * ac_count * ac_hours * 30 * temp_weight
            
        else:
            light_map = {"LED": 0.8, "LED와 일반조명 혼합": 1.1, "형광등·일반조명 중심": 1.4, "모름": 1.2}
            light_weight = light_map.get(answers.get("q14_light", "형광등·일반조명 중심"), 1.2)
            
            monthly_kwh = row["rated_power_kw"] * (pc_count / 20) * 12 * 30 * light_weight

        monthly_cost = monthly_kwh * KRW_PER_KWH
        monthly_carbon = monthly_kwh * CARBON_FACTOR
        
        results.append({
            "equipment": eq,
            "name": row["name"],
            "monthly_kwh": round(monthly_kwh, 2),
            "monthly_cost": round(monthly_cost),
            "monthly_carbon": round(monthly_carbon, 2)
        })
    return pd.DataFrame(results)

# 2. 백엔드: Python Rule Engine
def python_rule_engine(answers):
    diagnoses = []
    
    if answers.get("q4_pc_manage") in ["모니터만 끔", "둘 다 켜둠"]:
        diagnoses.append({
            "waste_code": "PC_STANDBY", "equipment": "PC_MONITOR", "risk_score": 90,
            "title": "손님 없는 빈 좌석의 PC·모니터 전원 방치",
            "description": "빈 좌석에서 본체나 모니터 전원을 켜둔 채 방치하여 불필요한 대기전력이 지속해서 소모되고 있습니다."
        })
        
    if answers.get("q9_temp") in ["22℃ 이하", "23~24℃"]:
        diagnoses.append({
            "waste_code": "HVAC_LOW_TEMP", "equipment": "HVAC", "risk_score": 85,
            "title": "에어컨 설정 온도 과도 저온 유지",
            "description": "실내 적정 온도(26℃)보다 낮게 설정되어 냉방 전력이 과다하게 소모되고 있습니다."
        })

    if answers.get("q11_filter") in ["3개월 초과", "거의 안 함"]:
        diagnoses.append({
            "waste_code": "FILTER_DIRTY", "equipment": "HVAC", "risk_score": 70,
            "title": "에어컨 필터 청소 주기가 김",
            "description": "필터 오염으로 인해 냉방 효율이 떨어지고 전력 소비량이 증가하고 있습니다."
        })

    if answers.get("q12_door") in ["자주 열려있음", "계속 열어둠"]:
        diagnoses.append({
            "waste_code": "DOOR_OPEN", "equipment": "HVAC", "risk_score": 80,
            "title": "냉방 중 출입문 개방으로 인한 냉기 손실",
            "description": "출입문이 열려 있어 냉기가 지속해서 유실되며 에어컨 부하가 가중되고 있습니다."
        })

    if answers.get("q13_lighting") == "계속 켜둠":
        diagnoses.append({
            "waste_code": "LIGHT_ON", "equipment": "LIGHTING", "risk_score": 60,
            "title": "손님이 없는 구역의 조명 상시 점등",
            "description": "이용객이 없는 구역까지 실내 조명이 계속 켜져 있어 전력이 낭비되고 있습니다."
        })

    if not diagnoses:
        diagnoses.append({
            "waste_code": "GENERAL_OPTIMIZE", "equipment": "LIGHTING", "risk_score": 40,
            "title": "전반적인 설비 대기전력 및 타이머 점검 필요",
            "description": "현재 양호한 상태이나 미세 전력 누수를 주기적으로 점검하는 것을 권장합니다."
        })
        
    return sorted(diagnoses, key=lambda x: x["risk_score"], reverse=True)

# 3. 백엔드: ChromaDB RAG
@st.cache_resource
def init_rag_db():
    client = chromadb.Client()
    col = client.get_or_create_collection(name="pc_bang_energy_guide")
    if col.count() == 0:
        col.add(ids=["doc_1"], documents=["[에너지공단] 컴퓨터 절전모드·모니터 끄기: 빈 좌석 자동 절전 또는 수동 소등으로 대기전력 원천 차단."], metadatas=[{"equipment": "PC_MONITOR"}])
        col.add(ids=["doc_2"], documents=["[에너지공단] 적정 냉방온도 유지: 실내 냉방 온도를 26℃로 유지하고 에어컨 운전 시간을 조절."], metadatas=[{"equipment": "HVAC"}])
        col.add(ids=["doc_3"], documents=["[에너지공단] 실내기 필터 세척·관리: 필터 주기적 청소 및 문 닫고 냉방하기로 냉기 손실 방지."], metadatas=[{"equipment": "HVAC"}])
        col.add(ids=["doc_4"], documents=["[에너지공단] 고효율 조명 이용 및 불필요한 조명 끄기: 미사용 구역 소등 및 LED 교체."], metadatas=[{"equipment": "LIGHTING"}])
    return col

rag_collection = init_rag_db()

def search_rag_guides(equipment_type):
    results = rag_collection.query(query_texts=["에너지 절감 방법 가이드"], n_results=1, where={"equipment": equipment_type})
    return results["documents"][0][0] if results["documents"] else "관련 공식 가이드가 없습니다."

# 4. 세션 상태 안전 초기화
if "step" not in st.session_state:
    st.session_state.step = 1
if "answers" not in st.session_state:
    st.session_state.answers = {
        "pc_count": 100, "op_hours": 24, "ac_count": 4, "ac_hours": 10,
        "q3_idle": "1~10%", "q4_pc_manage": "직접 종료", "q9_temp": "25℃",
        "q11_filter": "1 개월 초과~3 개월", "q12_door": "출입할 때만 열고 닫음",
        "q13_lighting": "구역별로 모두 끔", "q14_light": "형광등·일반조명 중심"
    }

# [페이지 1] 15가지 상세 설문 입력폼
if st.session_state.step == 1:
    st.title("⚡ PC방 에너지 진단 설문 (15개 문항)")
    st.write("제시된 표의 설문 항목에 맞춰 매장 운영 및 설비 관리 상태를 입력해 주세요.")
    
    with st.form("survey_15_form"):
        st.subheader("1 매장 운영과 빈 좌석 관리")
        pc_count = st.number_input("1. PC방 좌석은 총 몇 석인가요?", min_value=10, max_value=500, value=st.session_state.answers.get("pc_count", 100), step=10)
        op_hours = st.slider("2. 하루에 몇 시간 영업하시나요?", min_value=1, max_value=24, value=st.session_state.answers.get("op_hours", 24))
        q3_idle = st.radio("3. 영업시간 전체를 평균으로 보면 빈 좌석은 어느 정도인가요?", ["0%", "1~10%", "11~30%", "31~50%", "51% 이상", "모름"])
        q4_pc_manage = st.radio("4. 손님이 없는 좌석의 PC와 모니터는 어떻게 관리하시나요?", ["자동 절전", "자동 종료", "직접 종료", "모니터만 끔", "둘 다 켜둠", "모름"])
        
        st.subheader("2 장비 정보와 냉방 관리")
        q5_spec = st.radio("5. PC 한 대의 주요 사양은 어떻게 되나요?", ["일반형", "중고사양", "고사양", "여러 사양 혼합", "모름"])
        q6_power = st.text_input("6. PC 1 대의 전력 표시값을 알고 계신가요?", value="모름")
        q7_monitor = st.radio("7. 사용 중인 모니터 크기는 어느 정도인가요?", ["24인치 이하", "24인치 초과~27 인치", "27인치 초과~32 인치", "32 인치 초과", "혼합", "모름"])
        ac_count = st.number_input("8. 매장에 설치된 에어컨은 총 몇 대인가요?", min_value=0, max_value=30, value=st.session_state.answers.get("ac_count", 4))
        q9_temp = st.radio("9. 여름철 에어컨은 보통 몇 ℃로 설정하시나요?", ["22℃ 이하", "23~24℃", "25℃", "26℃ 이상", "모름", "미사용"])
        ac_hours = st.slider("10. 냉방하는 날에는 에어컨을 하루 평균 몇 시간 사용하시나요?", min_value=0, max_value=24, value=st.session_state.answers.get("ac_hours", 10))
        
        st.subheader("3 냉방 습관과 조명 및 월 사용량")
        q11_filter = st.radio("11. 에어컨 필터는 얼마나 자주 청소하시나요?", ["2 주 이내", "2 주 초과~1 개월", "1 개월 초과~3 개월", "3 개월 초과", "거의 안 함", "모름"])
        q12_door = st.radio("12. 냉방 중 출입문은 어떻게 관리하시나요?", ["출입할 때만 열고 닫음", "자주 열려있음", "계속 열어둠", "모름", "미사용"])
        q13_lighting = st.radio("13. 손님이 없는 구역의 조명은 어떻게 관리하시나요?", ["구역별로 모두 끔", "일부만 끔", "계속 켜둠", "빈 구역 없음", "모름"])
        q14_light = st.radio("14. 매장 조명은 대부분 어떤 종류인가요?", ["LED", "LED와 일반조명 혼합", "형광등·일반조명 중심", "모름"])
        q15_bill = st.text_input("15. 최근 한 달 전기사용량을 알고 계신가요?", value="모름")

        submitted = st.form_submit_button("AI 정밀 진단하기 🚀", use_container_width=True)
        if submitted:
            answers = {
                "pc_count": pc_count, "op_hours": op_hours,
                "q3_idle": q3_idle, "q4_pc_manage": q4_pc_manage,
                "q5_spec": q5_spec, "q6_power": q6_power,
                "q7_monitor": q7_monitor, "ac_count": ac_count,
                "q9_temp": q9_temp, "ac_hours": ac_hours,
                "q11_filter": q11_filter, "q12_door": q12_door,
                "q13_lighting": q13_lighting, "q14_light": q14_light,
                "q15_bill": q15_bill
            }
            st.session_state.answers = answers
            st.session_state.step = 2
            st.rerun()

# [페이지 2] AI 에너지 진단 결과
elif st.session_state.step == 2:
    st.title("🔍 AI 에너지 진단 결과")
    diagnoses = python_rule_engine(st.session_state.answers)
    
    if diagnoses:
        avg_risk = sum([d["risk_score"] for d in diagnoses]) / len(diagnoses)
        efficiency_score = max(30, int(100 - (avg_risk * 0.7)))
    else:
        efficiency_score = 90
        
    score_delta = efficiency_score - 100
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric(
            label="종합 에너지 효율 점수", 
            value=f"{efficiency_score}점", 
            delta=f"{score_delta}점 (개선 필요)" if efficiency_score < 80 else "매우 우수함", 
            delta_color="inverse"
        )
    with col2:
        st.info(f"💡 **AI 코치 진단**: 입력하신 **{st.session_state.answers.get('pc_count', 100)}석** 매장의 15개 설문 항목 분석 결과입니다.")
        
    st.subheader("🚨 가장 먼저 확인해야 할 영역 (Rule Engine + RAG)")
    for diag in diagnoses:
        guide_text = search_rag_guides(diag["equipment"])
        st.markdown(f"""
        <div style="background-color:#f8fafc; border:1px solid #e2e8f0; padding:15px; border-radius:10px; margin-bottom:10px;">
            <h4>{diag['title']} <span style="color:#ef4444; font-size:12px;">[위험점수: {diag['risk_score']}]</span></h4>
            <p style="color:#475569; margin:5px 0;">{diag['description']}</p>
            <hr style="margin:8px 0; border:0; border-top:1px solid #cbd5e1;">
            <p style="font-size:13px; color:#047857; margin:0;"><b>📘 에너지공단 RAG 근거:</b> {guide_text}</p>
        </div>
        """, unsafe_allow_html=True)
        
    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("⬅️ 설문 수정하기", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with col_next:
        if st.button("📈 예상 절감 효과 보기 ➔", use_container_width=True):
            st.session_state.step = 3
            st.rerun()

# [페이지 3] 예상 절감 효과 및 감액 상세 분석
# [페이지 3] 예상 절감 효과 및 감액 상세 분석 (텍스트 최적화 버전)
elif st.session_state.step == 3:
    pc_count_val = st.session_state.answers.get("pc_count", 100)
    st.title(f"📈 예상 절감 효과 상세 분석 ({pc_count_val}석 기준)")
    st.write("입력하신 매장 운영 정보 및 15개 진단 결과를 바탕으로 산출된 월간 전력 사용량 및 요금 감액 비교입니다.")
    
    eq_df = load_pc_bang_data()
    before_impact_df = calculate_energy_impact(st.session_state.answers, eq_df)
    
    optimized_answers = st.session_state.answers.copy()
    optimized_answers["q3_idle"] = "1~10%"
    optimized_answers["q4_pc_manage"] = "자동 절전"
    optimized_answers["q9_temp"] = "25℃"
    optimized_answers["q12_door"] = "출입할 때만 열고 닫음"
    optimized_answers["q13_lighting"] = "구역별로 모두 끔"
    
    after_impact_df = calculate_energy_impact(optimized_answers, eq_df)
    
    before_kwh = before_impact_df["monthly_kwh"].sum()
    after_kwh = after_impact_df["monthly_kwh"].sum()
    saved_kwh = before_kwh - after_kwh
    
    before_cost = before_impact_df["monthly_cost"].sum()
    after_cost = after_impact_df["monthly_cost"].sum()
    saved_cost = before_cost - after_cost
    
    before_carbon = before_impact_df["monthly_carbon"].sum()
    after_carbon = after_impact_df["monthly_carbon"].sum()
    saved_carbon = before_carbon - after_carbon
    
    # 텍스트가 잘리지 않도록 핵심만 간결하게 표현한 메트릭 카드 사용
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(
            label="월 전력 사용량", 
            value=f"{int(after_kwh):,} kWh", 
            delta=f"↓ {int(saved_kwh):,} 절감 (기존 {int(before_kwh):,})", 
            delta_color="normal"
        )
    with m2:
        st.metric(
            label="월 전기요금 감액", 
            value=f"{int(after_cost):,} 원", 
            delta=f"↓ {int(saved_cost):,}원 감액", 
            delta_color="normal"
        )
    with m3:
        st.metric(
            label="월 탄소 감축량", 
            value=f"{round(after_carbon, 1)} kg", 
            delta=f"↓ {round(saved_carbon, 1)} kg 감축", 
            delta_color="normal"
        )
        
    st.markdown("---")
    st.subheader("📊 설비별 전력 소비 비교 및 절감액 상세")
    
    comparison_df = pd.DataFrame({
        "설비명": before_impact_df["name"],
        "기존 전력(kWh)": before_impact_df["monthly_kwh"].apply(lambda x: f"{x:,.1f}"),
        "개선 후 전력(kWh)": after_impact_df["monthly_kwh"].apply(lambda x: f"{x:,.1f}"),
        "월 절감액(원)": (before_impact_df["monthly_cost"] - after_impact_df["monthly_cost"]).apply(lambda x: f"{int(x):,}")
    })
    
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
    if st.button("🔄 처음으로 돌아가기", use_container_width=True):
        st.session_state.step = 1
        st.rerun()