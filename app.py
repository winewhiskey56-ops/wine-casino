import streamlit as st
import google.generativeai as genai
import random

# --- 1. КОНФИГУРАЦИЯ ---
DATA = {
    "Сладость": ["сухое", "полусухое", "полусладкое", "сладкое"],
    "Страна": ["Россия", "ЮАР", "Австралия", "Аргентина", "США", "Новая Зеландия", "Чили", "Франция", "Италия", "Испания", "Австрия", "Германия", "Португалия", "Грузия", "Армения"],
    "Сорт винограда": ["Шардоне", "Рислинг", "Совиньон Блан", "Пино Гриджио", "Гевюрцтраминер", "Кортезе", "Гарганега", "Альбариньо", "Вердехо", "Грюнер Вельтлинер", "Каберне Совиньон", "Мерло", "Пино Нуар", "Сира/Шираз", "Темпранильо", "Санджовезе", "Мальбек", "Красностоп", "Саперави"],
    "Выдержка": ["выдержано в дубе", "не выдержано в дубе", "выдержано на осадке"],
    "Градус": ["11%", "12%", "13%", "14%"],
    "Год урожая": [str(year) for year in range(2015, 2027)]
}

COEFFS = {"Сладость": 2, "Выдержка": 2, "Страна": 3, "Сорт винограда": 3, "Градус": 4, "Год урожая": 5}

# --- 2. ИНИЦИАЛИЗАЦИЯ ИИ ---
def initialize_ai():
    try:
        if "GEMINI_API_KEY" not in st.secrets:
            return None, "Ключ API не найден в Secrets"
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        selected_model = next((m for m in ['models/gemini-1.5-flash', 'models/gemini-pro'] if m in available_models), available_models[0] if available_models else None)
        return (genai.GenerativeModel(selected_model), f"Активен: {selected_model}") if selected_model else (None, "Нет моделей")
    except Exception as e:
        return None, f"Ошибка ИИ: {str(e)}"

if "ai_model" not in st.session_state:
    model, status = initialize_ai()
    st.session_state.ai_model = model
    st.session_state.ai_status = status

def get_ai_hint(target_type, target_value):
    model = st.session_state.ai_model
    if not model: return "ИИ недоступен."
    
    seed = random.randint(1, 100000)
    prompt = f"Напиши сложный факт про {target_type} '{target_value}'. НЕ НАЗЫВАЙ '{target_value}'. БЕЗ ГЕОГРАФИИ (границы, соседи). БЕЗ ВКУСА. Только история/этимология. 2-3 предложения. Конец обязательно точкой. ID:{seed}"
    
    try:
        safety = [{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}]
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.8, max_output_tokens=1000), safety_settings=safety)
        res = response.text.strip()
        if not res.endswith(('.', '!', '?')):
            idx = max(res.rfind('.'), res.rfind('!'), res.rfind('?'))
            if idx != -1: res = res[:idx+1]
        return res
    except: return "Ошибка генерации. Попробуйте еще раз."

# --- 3. СОСТОЯНИЕ ИГРЫ ---
for key in ["players", "round_num", "page", "current_wine", "bet_rows_count", "hints", "current_player_idx"]:
    if key not in st.session_state:
        if key == "players": st.session_state[key] = []
        elif key == "round_num": st.session_state[key] = 1
        elif key == "page": st.session_state[key] = "registration"
        elif key == "current_wine": st.session_state[key] = {}
        elif key == "bet_rows_count": st.session_state[key] = 1
        elif key == "hints": st.session_state[key] = {"country": "", "grape": ""}
        elif key == "current_player_idx": st.session_state[key] = 0

def header():
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        try: st.image("logo.png", width=250)
        except: st.write("### WINE & WHISKEY")
    st.markdown("---")

# --- 4. СТРАНИЦЫ ---

def show_registration():
    header()
    st.markdown("<h2 style='text-align: center;'>📝 Регистрация</h2>", unsafe_allow_html=True)
    name = st.text_input("Имя игрока:", key="temp_name_input")
    if st.button("Добавить"):
        if name:
            st.session_state.players.append({"name": name, "balance": 1000, "round_bets": [], "balance_at_start": 1000})
            st.rerun()
    
    if st.session_state.players:
        for p in st.session_state.players: st.write(f"✅ {p['name']}")
        if st.button("Начать ➔", use_container_width=True, type="primary"):
            st.session_state.page = "setup"; st.rerun()

def show_setup():
    header()
    st.markdown(f"### 🍷 Раунд №{st.session_state.round_num}")
    for cat, opts in DATA.items():
        st.session_state.current_wine[cat] = st.selectbox(f"{cat}:", ["—"] + opts, key=f"setup_{cat}")
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    if c1.button("🤖 Намек на Страну"):
        val = st.session_state.current_wine.get("Страна")
        if val != "—": st.session_state.hints["country"] = get_ai_hint("страну", val)
    if c2.button("🤖 Намек на Сорт"):
        val = st.session_state.current_wine.get("Сорт винограда")
        if val != "—": st.session_state.hints["grape"] = get_ai_hint("сорт винограда", val)

    if st.session_state.hints["country"]: st.info(st.session_state.hints["country"])
    if st.session_state.hints["grape"]: st.success(st.session_state.hints["grape"])

    if st.button("К ставкам ➔", use_container_width=True, type="primary"):
        for p in st.session_state.players: p['balance_at_start'] = p['balance']
        st.session_state.page = "betting"
        st.session_state.current_player_idx = 0
        st.session_state.bet_rows_count = 1
        st.rerun()

def show_betting():
    header()
    if not st.session_state.players:
        st.error("Нет игроков!"); return

    p_idx = st.session_state.current_player_idx
    player = st.session_state.players[p_idx]
    
    # Считаем текущие ставки в реальном времени
    temp_spent = 0
    valid_bets = []
    for i in range(st.session_state.bet_rows_count):
        c_cat = st.session_state.get(f"p{p_idx}_c{i}", "Сладость")
        c_val = st.session_state.get(f"p{p_idx}_v{i}", "—")
        c_amt = st.session_state.get(f"p{p_idx}_a{i}", 0)
        if c_val != "—" and c_amt > 0:
            temp_spent += c_amt
            valid_bets.append({"cat": c_cat, "val": c_val, "amt": c_amt})

    st.markdown(f"<h2 style='text-align: center;'>👤 {player['name']}</h2>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; color: gold;'>Баланс: {player['balance'] - temp_spent}</h3>", unsafe_allow_html=True)

    for i in range(st.session_state.bet_rows_count):
        c1, c2, c3 = st.columns([2, 2, 1])
        cat = c1.selectbox("Параметр", list(COEFFS.keys()), key=f"p{p_idx}_c{i}")
        val = c2.selectbox("Ставка", ["—"] + DATA[cat], key=f"p{p_idx}_v{i}")
        amt = c3.number_input("С
