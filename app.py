import streamlit as st
import google.generativeai as genai
import random

# --- 1. КОНФИГУРАЦИЯ ДАННЫХ ---
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
        if selected_model:
            return genai.GenerativeModel(selected_model), f"Модель: {selected_model}"
        return None, "Нет доступных моделей"
    except Exception as e:
        return None, f"Ошибка ИИ: {str(e)}"

if "ai_model" not in st.session_state:
    model, status = initialize_ai()
    st.session_state.ai_model = model
    st.session_state.ai_status = status

def get_ai_hint(target_type, target_value):
    model = st.session_state.ai_model
    if not model: return "ИИ недоступен. Проверьте настройки."
    
    seed = random.randint(1, 100000)
    
    if "страну" in target_type.lower():
        rules = "ЗАПРЕЩЕНО: части света, соседи, горы/моря, столицы, флаги, лидеры. ТЕМА: этимология, редкая история, культура."
    else:
        rules = "ЗАПРЕЩЕНО: вкус, запах, цвет, страны производства. ТЕМА: ботаника, генетика, легенды названия."

    prompt = f"""
    Напиши один сложный факт про {target_type} '{target_value}'.
    ID: {seed}
    ПРАВИЛА:
    1. НЕ НАЗЫВАЙ '{target_value}'.
    2. {rules}
    3. Только достоверная информация.
    4. 2-3 полных предложения. ОБЯЗАТЕЛЬНО закончи точкой.
    5. Никаких вступлений.
    """
    
    try:
        safety = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
        response = model.generate_content(
            prompt, 
            generation_config=genai.types.GenerationConfig(temperature=0.8, max_output_tokens=1000),
            safety_settings=safety
        )
        res = response.text.strip().replace('"', '')
        if not res.endswith(('.', '!', '?')):
            idx = max(res.rfind('.'), res.rfind('!'), res.rfind('?'))
            if idx != -1: res = res[:idx+1]
        return res
    except:
        return "Не удалось получить сложный факт. Попробуйте еще раз!"

# --- 3. УПРАВЛЕНИЕ СОСТОЯНИЕМ ---
state_keys = {
    "players": [], "page": "registration", "round_num": 1,
    "current_wine": {}, "bet_rows_count": 1,
    "hints": {"country": "", "grape": ""}, "current_player_idx": 0,
    "temp_name_input": "" # Добавили ключ для строки регистрации
}
for key, default in state_keys.items():
    if key not in st.session_state:
        st.session_state[key] = default

def header():
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        try: st.image("logo.png", width=250)
        except: st.write("### WINE & WHISKEY")
    st.markdown("---")

# --- 4. СТРАНИЦЫ ---

def add_player():
    name = st.session_state.temp_name_input.strip()
    if name:
        st.session_state.players.append({"name": name, "balance": 1000, "round_bets": [], "balance_at_start": 1000})
        st.session_state.temp_name_input = "" # Очищаем поле после добавления

def show_registration():
    header()
    st.markdown("<h2 style='text-align: center;'>📝 Регистрация</h2>", unsafe_allow_html=True)
    
    # Теперь работает и по нажатию Enter, и очищается после добавления
    st.text_input("Имя игрока (нажмите Enter для добавления):", key="temp_name_input", on_change=add_player)
    
    if st.button("Добавить игрока"):
        add_player()
        st.rerun()
    
    if st.session_state.players:
        for p in st.session_state.players: st.write(f"✅ {p['name']}")
        if st.button("Начать игру ➔", use_container_width=True, type="primary"):
            st.session_state.page = "setup"
            st.rerun()

def show_setup():
    header()
    st.markdown(f"### 🍷 Раунд №{st.session_state.round_num}")
    
    with st.expander("Параметры вина", expanded=True):
        for cat, opts in DATA.items():
            st.session_state.current_wine[cat] = st.selectbox(f"{cat}:", ["—"] + opts, key=f"s_{cat}")
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    if c1.button("🤖 Факт о Стране"):
        val = st.session_state.current_wine.get("Страна")
        if val != "—": 
            with st.spinner("Ищу факт..."):
                st.session_state.hints["country"] = get_ai_hint("страну", val)
    
    if c2.button("🤖 Факт о Сорте"):
        val = st.session_state.current_wine.get("Сорт винограда")
        if val != "—": 
            with st.spinner("Ищу факт..."):
                st.session_state.hints["grape"] = get_ai_hint("сорт винограда", val)

    if st.session_state.hints["country"]: st.info(st.session_state.hints["country"])
    if st.session_state.hints["grape"]: st.success(st.session_state.hints["grape"])

    if st.button("Перейти к ставкам ➔", use_container_width=True, type="primary"):
        for p in st.session_state.players: p['balance_at_start'] = p['balance']
        st.session_state.page = "betting"
        st.session_state.current_player_idx = 0
        st.session_state.bet_rows_count = 1
        st.rerun()

def show_betting():
    header()
    p_idx = st.session_state.current_player_idx
    player = st.session_state.players[p_idx]
    
    temp_spent = 0
    valid_bets = []
    for i in range(st.session_state.bet_rows_count):
        cat = st.session_state.get(f"p{p_idx}_c{i}", "Сладость")
        val = st.session_state.get(f"p{p_idx}_v{i}", "—")
        amt = st.session_state.get(f"p{p_idx}_a{i}", 0)
        if val != "—" and amt > 0:
            temp_spent += amt
            valid_bets.append({"cat": cat, "val": val, "amt": amt})

    st.markdown(f"<h2 style='text-align: center;'>👤 {player['name']}</h2>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; color: #D4AF37;'>Остаток: {player['balance'] - temp_spent}</h3>", unsafe_allow_html=True)

    for i in range(st.session_state.bet_rows_count):
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1: st.selectbox("Тип", list(COEFFS.keys()), key=f"p{p_idx}_c{i}")
        with c2: st.selectbox("Ставка", ["—"] + DATA[st.session_state[f"p{p_idx}_c{i}"]], key=f"p{p_idx}_v{i}")
        with c3: st.number_input("Сумма", min_value=0, step=50, key=f"p{p_idx}_a{i}")
        
        current_v = st.session_state.get(f"p{p_idx}_v{i}", "—")
        current_a = st.session_state.get(f"p{p_idx}_a{i}", 0)
        if i == st.session_state.bet_rows_count - 1 and current_v != "—" and current_a > 0:
            st.session_state.bet_rows_count += 1
            st.rerun()

    if st.button("Принять ставки", use_container_width=True, type="primary"):
        player['round_bets'] = valid_bets
        player['balance'] -= temp_spent
        if st.session_state.current_player_idx < len(st.session_state.players) - 1:
            st.session_state.current_player_idx += 1
            st.session_state.bet_rows_count = 1
        else:
            st.session_state.page = "results"
        st.rerun()

def show_results():
    header()
    correct = st.session_state.current_wine
    st.markdown("<h2 style='text-align: center;'>📊 Итоги Раунда</h2>", unsafe_allow_html=True)
    st.info("🎯 **Правильный ответ:** " + " | ".join([f"{k}: {v}" for k, v in correct.items() if v != "—"]))
    
    # Возвращаем детальную статистику
    for p in st.session_state.players:
        win_sum = 0
        details = []
        for b in p['round_bets']:
            is_hit = str(b['val']).lower() == str(correct.get(b['cat'])).lower()
            res = b['amt'] * COEFFS[b['cat']] if is_hit else 0
            win_sum += res
            details.append(f"<p style='color:{'#28a745' if is_hit else '#dc3545'}; margin: 0;'>{'✅' if is_hit else '❌'} {b['cat']}: {b['val']} | {b['amt']} ➔ {res}</p>")
        
        p['balance'] += win_sum
        with st.expander(f"👤 {p['name']} | Выигрыш: +{win_sum}"):
            st.markdown("".join(details) or "Ставок нет", unsafe_allow_html=True)
            st.markdown("---")
            st.write(f"**До:** {p['balance_at_start']} | **Стало:** {p['balance']}")

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    if c1.button("Следующий раунд 🍷", use_container_width=True):
        st.session_state.round_num += 1
        st.session_state.page = "setup"
        st.session_state.hints = {"country": "", "grape": ""}
        for k in list(st.session_state.keys()):
            if any(x in k for x in ["_v", "_a", "_c"]): del st.session_state[k]
        st.rerun()
        
    # Кнопка перехода к финалу
    if c2.button("Завершить игру 🏆", use_container_width=True, type="primary"):
        st.session_state.page = "final"
        st.rerun()

def show_final():
    header()
    st.markdown("<h1 style='text-align: center;'>🏆 Финал Игры</h1>", unsafe_allow_html=True)
    
    sorted_players = sorted(st.session_state.players, key=lambda x: x['balance'], reverse=True)
    for i, p in enumerate(sorted_players):
        # Подсветка победителя
        if i == 0:
            st.success(f"🥇 1. {p['name']} — {p['balance']} очков")
        elif i == 1:
            st.info(f"🥈 2. {p['name']} — {p['balance']} очков")
        elif i == 2:
            st.warning(f"🥉 3. {p['name']} — {p['balance']} очков")
        else:
            st.write(f"**{i+1}. {p['name']}** — {p['balance']} очков")
            
    st.markdown("---")
    if st.button("Начать новую игру 🔄", use_container_width=True, type="primary"):
        st.session_state.clear()
        st.rerun()

# --- 5. РОУТИНГ ---
if st.session_state.page == "registration": show_registration()
elif st.session_state.page == "setup": show_setup()
elif st.session_state.page == "betting": show_betting()
elif st.session_state.page == "results": show_results()
elif st.session_state.page == "final": show_final()
