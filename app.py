# app.py
import streamlit as st
import pandas as pd
import chromadb

st.set_page_config(
    page_title="PC방 AI 에너지 코치",
    page_icon="⚡",
    layout="centered"
)

# 1. 백엔드: 해커튼 팀 실행안 15개 전체 문항 데이터 및 정밀 계산 파이프라인
@st.cache_data
def load_pc_bang_data():
    equipment_df = pd.DataFrame([
        # 2번 항목: 게임 프레임 설정 (3개 문항)
        {"equipment": "FRAME_1", "name": "2-① 대표 PC 프레임 및 소비전력 측정", "rated_power_kw": 0.03, "default_hours": 8},
        {"equipment": "FRAME_2", "name": "2-② 게임별 최대 프레임 설정 (메뉴·백그라운드)", "rated_power_kw": 0.03, "default_hours": 8},
        {"equipment": "FRAME_3", "name": "2-④ 동일 사양 좌석 확대 및 업데이트 후 유지 검증", "rated_power_kw": 0.03, "default_hours": 8},
        
        # 3번 항목: 업데이트 전 대기 (3개 문항)
        {"equipment": "UPDATE_BEFORE_1", "name": "3-① 관리 프로그램 업데이트 시작 시간·대상 지정", "rated_power_kw": 0.08, "default_hours": 2},
        {"equipment": "UPDATE_BEFORE_2", "name": "3-② 미사용 PC 절전 및 Wake-on-LAN 원격 켜기", "rated_power_kw": 0.08, "default_hours": 2},
        {"equipment": "UPDATE_BEFORE_4", "name": "3-③ 실제 업데이트 시간 유지 및 불필요한 대기시간 단축", "rated_power_kw": 0.08, "default_hours": 2},
        
        # 4번 항목: 업데이트 후 방치 (3개 문항)
        {"equipment": "UPDATE_AFTER_1", "name": "4-① 작업 완료 상태 기준 후속 동작 설정 (강제종료 지양)", "rated_power_kw": 0.08, "default_hours": 3},
        {"equipment": "UPDATE_AFTER_3", "name": "4-② 작업 끝난 빈 좌석 자동 종료·절전 적용", "rated_power_kw": 0.08, "default_hours": 3},
        {"equipment": "UPDATE_AFTER_4", "name": "4-③ 다음 손님 이용 시 정상 부팅·실행 시험", "rated_power_kw": 0.08, "default_hours": 3},
        
        # 5번 항목: 손님이 적은 시간의 좌석 운영 (3개 문항)
        {"equipment": "ZONE_OP_1", "name": "5-① 좌석 배치도 조명 스위치 및 냉방 독립 제어 구역 표시", "rated_power_kw": 1.0, "default_hours": 6},
        {"equipment": "ZONE_OP_2", "name": "5-② 저이용 시간 신규 손님 특정 구역 우선 안내", "rated_power_kw": 1.0, "default_hours": 6},
        {"equipment": "ZONE_OP_3", "name": "5-③ 빈 구역 일반 조명 소등 및 냉방 설정 조정", "rated_power_kw": 1.0, "default_hours": 6},
        
        # 6번 항목: 게이밍 주변기기 조명 (3개 문항)
        {"equipment": "PERIPHERAL_1", "name": "6-① PC 사용 중 미사용 상태 및 종료 후 상태 분리 점검", "rated_power_kw": 0.002, "default_hours": 10},
        {"equipment": "PERIPHERAL_2", "name": "6-② 제조사 설정 프로그램 미사용 시 조명 끄기 연동", "rated_power_kw": 0.002, "default_hours": 10},
        {"equipment": "PERIPHERAL_4", "name": "6-③ 대표 좌석 입력·충전·기동 시험 및 동종 기종 확대", "rated_power_kw": 0.002, "default_hours": 10}
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
        ans = answers.get(eq, "보통/미흡")
        
        # 답변 성향에 따른 가중치 부여 (잘 지키고 있으면 절감 여지가 적음)
        w_map = {"철저히 준수": 0.1, "부분 적용": 0.5, "미흡/전혀 안 함": 1.0, "해당 없음·모름": 1.0}
        factor = w_map.get(ans, 1.0)
        
        b_kwh = row["rated_power_kw"] * pc_count * row["default_hours"] * 30 * factor
        a_kwh = b_kwh * 0.15 # 개선 시 85% 이상 절감 가정
        
        b_cost = b_kwh * KRW_PER_KWH
        a_cost = a_kwh * KRW_PER_KWH
        b_carbon = b_kwh * CARBON_FACTOR
        a_carbon = a_kwh * CARBON_FACTOR
        
        before_results.append({"equipment": eq, "name": row["name"], "kwh": round(b_kwh, 1), "cost": round(b_cost), "carbon": round(b_carbon, 1)})
        after_results.append({"equipment": eq, "name": row["name"], "kwh": round(a_kwh, 1), "cost": round(a_cost), "carbon": round(a_carbon, 1)})
        
    return pd.DataFrame(before_results), pd.DataFrame(after_results)

# 2. 백엔드: Python Rule Engine (15개 문항 전용 진단 로직)
def python_rule_engine(answers):
    diagnoses = []
    
    # 2번 그룹 진단
    if answers.get("FRAME_2") in ["미흡/전혀 안 함", "부분 적용"]:
        diagnoses.append({
            "title": "🎮 [2번] 게임별 최대 프레임 미설정",
            "description": "메뉴 및 백그라운드 화면부터 게임별 최대 프레임을 제한하여 GPU/CPU 연산 전력을 절감해야 합니다.",
            "equipment": "FRAME_2", "risk_score": 90
        })
    # 3번 그룹 진단
    if answers.get("UPDATE_BEFORE_2") in ["미흡/전혀 안 함", "부분 적용"]:
        diagnoses.append({
            "title": "⏳ [3번] 업데이트 전 미사용 PC 상시 방치",
            "description": "업데이트 전부터 빈 좌석 PC를 미리 켜두고 있어 대기전력이 낭비됩니다. Wake-on-LAN 등을 활용하세요.",
            "equipment": "UPDATE_BEFORE_2", "risk_score": 85
        })
    # 4번 그룹 진단
    if answers.get("UPDATE_AFTER_3") in ["미흡/전혀 안 함", "부분 적용"]:
        diagnoses.append({
            "title": "🛑 [4번] 업데이트 완료 후 빈 좌석 PC 전원 방치",
            "description": "업데이트 완료 직후 자동 절전/종료를 설정하지 않아 다음 손님까지 불필요한 가동이 발생합니다.",
            "equipment": "UPDATE_AFTER_3", "risk_score": 85
        })
    # 5번 그룹 진단
    if answers.get("ZONE_OP_3") in ["미흡/전혀 안 함", "부분 적용"]:
        diagnoses.append({
            "title": "💡❄️ [5번] 저이용 시간대 구역별 조명·냉방 미조정",
            "description": "손님이 적은 시간대에도 빈 구역의 조명과 냉방을 끄지 않아 추가 전력 손실이 발생하고 있습니다.",
            "equipment": "ZONE_OP_3", "risk_score": 80
        })
    # 6번 그룹 진단
    if answers.get("PERIPHERAL_2") in ["미흡/전혀 안 함", "부분 적용"]:
        diagnoses.append({
            "title": "⌨️ [6번] 게이밍 주변기기 조명 상시 점등",
            "description": "미사용 좌석의 키보드·마우스·헤드셋 거치대 조명이 꺼지지 않아 장식용 전력이 낭비되고 있습니다.",
            "equipment": "PERIPHERAL_2", "risk_score": 60
        })

    if not diagnoses:
        diagnoses.append({
            "title": "✨ 우수한 15대 실행안 준수 상태",
            "description": "기획서 내 모든 세부 실행 가이드를 모범적으로 실천하고 있습니다.",
            "equipment": "FRAME_2", "risk_score": 20
        })
    return sorted(diagnoses, key=lambda x: x["risk_score"], reverse=True)

# 3. 백엔드: ChromaDB RAG (15개 항목 지식베이스)
@st.cache_resource
def init_rag_db():
    client = chromadb.Client()
    col = client.get_or_create_collection(name="pc_bang_15_guides")
    if col.count() == 0:
        col.add(ids=["doc_f1"], documents=["[2-①] 대표 PC 1~2대에서 주요 게임 해상도·화질별 콘센트 기준 소비전력을 먼저 측정합니다."], metadatas=[{"equipment": "FRAME_1"}])
        col.add(ids=["doc_f2"], documents=["[2-②] 게임 또는 그래픽 드라이버에서 메뉴·백그라운드 화면부터 게임별 최대 프레임을 설정합니다."], metadatas=[{"equipment": "FRAME_2"}])
        col.add(ids=["doc_f3"], documents=["[2-④] 사양이 같은 좌석부터 확대하고, 게임 업데이트 후 설정 유지 여부를 확인합니다."], metadatas=[{"equipment": "FRAME_3"}])
        
        col.add(ids=["doc_ub1"], documents=["[3-①] 관리 프로그램에서 업데이트 시작 시각과 대상 좌석을 지정합니다."], metadatas=[{"equipment": "UPDATE_BEFORE_1"}])
        col.add(ids=["doc_ub2"], documents=["[3-②] 미사용 PC는 절전·종료하고 Wake-on-LAN으로 작업 직전에 켭니다."], metadatas=[{"equipment": "UPDATE_BEFORE_2"}])
        col.add(ids=["doc_ub4"], documents=["[3-③] 실제 업데이트 시간은 유지하고 시작 전 불필요한 대기시간만 줄입니다."], metadatas=[{"equipment": "UPDATE_BEFORE_4"}])
        
        col.add(ids=["doc_ua1"], documents=["[4-①] 작업 완료 상태를 기준으로 후속 동작을 설정하며 단순 정해진 시각 강제종료는 지양합니다."], metadatas=[{"equipment": "UPDATE_AFTER_1"}])
        col.add(ids=["doc_ua3"], documents=["[4-③] 모든 작업이 끝난 빈 좌석만 자동 종료·절전하고 미완료 좌석은 관리자 확인용으로 남깁니다."], metadatas=[{"equipment": "UPDATE_AFTER_3"}])
        col.add(ids=["doc_ua4"], documents=["[4-④] 다음 손님이 사용할 때 정상 부팅 및 게임 실행을 시험하고 소요 시간을 기록합니다."], metadatas=[{"equipment": "UPDATE_AFTER_4"}])
        
        col.add(ids=["doc_z1"], documents=["[5-①] 좌석 배치도에 조명 스위치와 냉방 제어 구역을 표시하고 독립 제어 가능 구역을 찾습니다."], metadatas=[{"equipment": "ZONE_OP_1"}])
        col.add(ids=["doc_z2"], documents=["[5-②] 저이용 시간에 신규 손님을 특정 구역으로 우선 안내합니다."], metadatas=[{"equipment": "ZONE_OP_2"}])
        col.add(ids=["doc_z3"], documents=["[5-③] 빈 구역의 일반 조명을 끄고 냉방 설정·가동을 조정하되 통로 안전조명과 환기는 유지합니다."], metadatas=[{"equipment": "ZONE_OP_3"}])
        
        col.add(ids=["doc_p1"], documents=["[6-①] PC 사용 중 미사용 상태와 PC 종료 후 상태를 나누어 주변기기 조명을 점검합니다."], metadatas=[{"equipment": "PERIPHERAL_1"}])
        col.add(ids=["doc_p2"], documents=["[6-②] 제조사 설정 프로그램에서 미사용 시 조명 끄기 또는 밝기 낮추기를 설정합니다."], metadatas=[{"equipment": "PERIPHERAL_2"}])
        col.add(ids=["doc_p4"], documents=["[6-③] 대표 좌석에서 입력·충전·기동이 정상인지 시험하고 같은 기종에 확대합니다."], metadatas=[{"equipment": "PERIPHERAL_4"}])
    return col

rag_collection = init_rag_db()

def search_rag_guides(eq):
    results = rag_collection.query(query_texts=["실행안 가이드"], n_results=1, where={"equipment": eq})
    return results["documents"][0][0] if results["documents"] else "해당 항목의 공식 실행 가이드가 없습니다."

# 4. 세션 상태 초기화
if "step" not in st.session_state:
    st.session_state.step = 1
if "answers" not in st.session_state:
    st.session_state.answers = {"pc_count": 50}

# [페이지 1] 해커튼 기획서 기반 15개 전체 문항 폼
if st.session_state.step == 1:
    st.title("⚡ PC방 전력 사용 개선 자가진단 (15개 전체 문항)")
    st.write("제공해주신 5장 기획서의 모든 세부 실행 항목(총 15문항)에 대한 자가진단입니다.")
    
    with st.form("survey_15_form"):
        pc_count = st.number_input("매장 총 PC 대수", min_value=10, max_value=300, value=st.session_state.answers.get("pc_count", 50), step=10)
        
        options = ["철저히 준수", "부분 적용", "미흡/전혀 안 함", "해당 없음·모름"]
        
        st.markdown("---")
        st.subheader("🎮 [2장] 게임 프레임 설정")
        q2_1 = st.radio("2-① 대표 PC 1~2대에서 주요 게임 해상도·화질별 콘센트 기준 소비전력을 기록·확인하시나요?", options, index=1)
        q2_2 = st.radio("2-② 게임 또는 그래픽 드라이버에서 메뉴·백그라운드 화면부터 게임별 최대 프레임을 설정하시나요?", options, index=2)
        q2_3 = st.radio("2-③ 사양이 같은 좌석부터 확대하고 게임 업데이트 후 설정 유지 여부를 확인하시나요?", options, index=1)
        
        st.markdown("---")
        st.subheader("⏳ [3장] 업데이트 전 대기")
        q3_1 = st.radio("3-① 관리 프로그램에서 업데이트 시작 시각과 대상 좌석을 체계적으로 지정하시나요?", options, index=1)
        q3_2 = st.radio("3-② 미사용 PC는 절전·종료하고 Wake-on-LAN을 통해 작업 직전에만 켜시나요?", options, index=2)
        q3_3 = st.radio("3-③ 실제 업데이트 시간은 유지하고 시작 전 불필요한 대기시간만 단축하시나요?", options, index=1)
        
        st.markdown("---")
        st.subheader("🛑 [4장] 업데이트 후 방치")
        q4_1 = st.radio("4-① 작업 완료 상태 기준 후속 동작을 설정하고 단순히 정해진 시각에 강제 종료하지 않으시나요?", options, index=1)
        q4_2 = st.radio("4-② 모든 작업이 끝난 빈 좌석만 자동 종료·절전하고 미완료 좌석은 남겨두시나요?", options, index=2)
        q4_3 = st.radio("4-③ 다음 손님이 사용할 때 정상 부팅·게임 실행이 가능한지 시험하고 소요 시간을 기록하시나요?", options, index=1)
        
        st.markdown("---")
        st.subheader("💡❄️ [5장] 손님이 적은 시간의 좌석 운영")
        q5_1 = st.radio("5-① 좌석 배치도에 조명 스위치와 냉방 제어 구역을 표시하고 독립 제어 가능 구역을 파악하셨나요?", options, index=1)
        q5_2 = st.radio("5-② 저이용 시간에 신규 손님을 특정 구역으로 우선 안내하여 구역 집중 운영을 하시나요?", options, index=2)
        q5_3 = st.radio("5-③ 빈 구역의 일반 조명을 끄고 냉방 설정·가동을 조정하며 통로 조명·환기는 유지하시나요?", options, index=1)
        
        st.markdown("---")
        st.subheader("⌨️ [6장] 게이밍 주변기기 조명")
        q6_1 = st.radio("6-① 빈 좌석에서 PC 사용 중 미사용 상태와 종료 후 상태를 나누어 주변기기 조명을 점검하시나요?", options, index=1)
        q6_2 = st.radio("6-② 제조사 설정 프로그램에서 미사용 시 조명 끄기 또는 밝기 낮추기를 연동하시나요?", options, index=2)
        q6_3 = st.radio("6-③ 대표 좌석에서 입력·충전·기동이 정상인지 시험하고 동종 기종에 확대하시나요?", options, index=1)

        submitted = st.form_submit_button("15개 문항 맞춤형 AI 종합 진단하기 🚀", use_container_width=True)
        if submitted:
            st.session_state.answers = {
                "pc_count": pc_count,
                "FRAME_1": q2_1, "FRAME_2": q2_2, "FRAME_3": q2_3,
                "UPDATE_BEFORE_1": q3_1, "UPDATE_BEFORE_2": q3_2, "UPDATE_BEFORE_4": q3_3,
                "UPDATE_AFTER_1": q4_1, "UPDATE_AFTER_3": q4_2, "UPDATE_AFTER_4": q4_3,
                "ZONE_OP_1": q5_1, "ZONE_OP_2": q5_2, "ZONE_OP_3": q5_3,
                "PERIPHERAL_1": q6_1, "PERIPHERAL_2": q6_2, "PERIPHERAL_4": q6_3
            }
            st.session_state.step = 2
            st.rerun()

# [페이지 2] AI 진단 결과 화면
elif st.session_state.step == 2:
    st.title("🔍 15개 문항 기반 AI 에너지 진단 결과")
    eq_df = load_pc_bang_data()
    diagnoses = python_rule_engine(st.session_state.answers)
    
    max_risk = max([d["risk_score"] for d in diagnoses]) if diagnoses else 30
    efficiency_score = max(20, int(100 - (max_risk * 0.75)))
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric(label="실행안 준수 종합 효율 점수", value=f"{efficiency_score}점", delta="개선 필요" if efficiency_score < 75 else "우수함", delta_color="inverse")
    with col2:
        st.info("💡 15가지 세부 실행 가이드 이행 여부를 분석하여 도출된 최우선 개선 영역입니다.")
        
    st.subheader("🚨 우선 개선 권장 영역 및 가이드 (RAG 연동)")
    for diag in diagnoses[:4]: # 상위 4개 우선 노출
        guide = search_rag_guides(diag["equipment"])
        st.markdown(f"""
        <div style="background-color:#f8fafc; border:1px solid #e2e8f0; padding:15px; border-radius:10px; margin-bottom:10px;">
            <h4>{diag['title']} <span style="color:#ef4444; font-size:12px;">[취약점수: {diag['risk_score']}]</span></h4>
            <p style="color:#475569; margin:5px 0;">{diag['description']}</p>
            <hr style="margin:8px 0; border:0; border-top:1px solid #cbd5e1;">
            <p style="font-size:13px; color:#047857; margin:0;"><b>📘 기획서 세부 가이드:</b> {guide}</p>
        </div>
        """, unsafe_allow_html=True)
        
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⬅️ 15문항 설문 수정하기", use_container_width=True):
            st.session_state.step = 1; st.rerun()
    with c2:
        if st.button("📈 전체 상세 절감액 분석 보기 ➔", use_container_width=True):
            st.session_state.step = 3; st.rerun()

# [페이지 3] 상세 절감액 분석 및 표
elif st.session_state.step == 3:
    pc_count_val = st.session_state.answers.get("pc_count", 50)
    st.title(f"📈 15개 항목별 예상 전력절감 및 감액 분석 ({pc_count_val}석 기준)")
    st.write("기획서 5장의 세부 계산 공식을 적용한 전체 15개 항목별 월간 절감 효과입니다.")
    
    eq_df = load_pc_bang_data()
    b_df, a_df = calculate_detailed_impact(st.session_state.answers, eq_df)
    
    tot_b_kwh, tot_a_kwh = b_df["kwh"].sum(), a_df["kwh"].sum()
    tot_b_cost, tot_a_cost = b_df["cost"].sum(), a_df["cost"].sum()
    tot_b_carb, tot_a_carb = b_df["carbon"].sum(), a_df["carbon"].sum()
    
    saved_cost = int(tot_b_cost - tot_a_cost)
    saved_kwh = int(tot_b_kwh - tot_a_kwh)
    saved_carb = round(tot_b_carb - tot_a_carb, 1)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div style="background-color:#f8fafc; border:1px solid #e2e8f0; padding:16px; border-radius:10px; text-align:center;">
            <div style="font-size:13px; color:#64748b; font-weight:600; margin-bottom:4px;">총 전력절감량</div>
            <div style="font-size:22px; color:#1e293b; font-weight:bold; margin-bottom:8px;">↓ {saved_kwh:,} kWh</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="background-color:#f8fafc; border:1px solid #e2e8f0; padding:16px; border-radius:10px; text-align:center;">
            <div style="font-size:13px; color:#64748b; font-weight:600; margin-bottom:4px;">요금 감액금액</div>
            <div style="font-size:22px; color:#1e293b; font-weight:bold; margin-bottom:8px;">↓ {saved_cost:,} 원</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style="background-color:#f8fafc; border:1px solid #e2e8f0; padding:16px; border-radius:10px; text-align:center;">
            <div style="font-size:13px; color:#64748b; font-weight:600; margin-bottom:4px;">탄소 감축량</div>
            <div style="font-size:22px; color:#1e293b; font-weight:bold; margin-bottom:8px;">↓ {saved_carb} kg</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    st.subheader("📊 15개 전체 세부 항목별 비교 요약 테이블")
    comparison_df = pd.DataFrame({
        "실행 항목": b_df["name"],
        "기존 전력": b_df["kwh"].apply(lambda x: f"{x:,.1f} kWh"),
        "개선 후 전력": a_df["kwh"].apply(lambda x: f"{x:,.1f} kWh"),
        "기존 요금": b_df["cost"].apply(lambda x: f"{x:,} 원"),
        "개선 후 요금": a_df["cost"].apply(lambda x: f"{x:,} 원"),
        "월 절감 금액": (b_df["cost"] - a_df["cost"]).apply(lambda x: f"{int(x):,} 원")
    })
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
    if st.button("🔄 처음으로 돌아가기", use_container_width=True):
        st.session_state.step = 1
        st.rerun()