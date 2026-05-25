import streamlit as st
import google.generativeai as genai
import random

# --- 1. КОНФИГУРАЦИЯ ДАННЫХ ---
DATA = {
    "Сладость": ["сухое", "полусухое", "полусладкое", "сладкое"],
    "Страна": ["Россия", "ЮАР", "Австралия", "Аргентина", "США", "Новая Зеландия", "Чили", "Франция", "Италия", "Испания", "Австрия", "Германия", "Португалия", "Грузия", "Армения"],
    "Сорт винограда": ["Шардоне", "Рислинг", "Совиньон Блан", "Пино Гриджио", "Гевюрцтраминер", "Кортезе", "Гарганега", "Альбариньо", "Вердехо", "Грюнер Вельтлинер", "Каберне Совиньон", "Мерло", "Пино Нуар", "Сира/Шираз", "Темпранильо", "Санджовезе", "Мальбек", "Красностоп", "Саперави"],
    "Выдержка": ["выдержано в дубе", "не выдержано в дубе", "выдержано на осадке"]
}

COEFFS = {"Страна": 2, "Сорт винограда": 3, "Сладость": 2, "Выдержка": 3}

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
    if not model: return "ИИ временно ушел в погреб. Проверьте API-ключ."
    
    seed = random.randint(1, 100000)
    
    if "страну" in target_type.lower():
        logic = """
        Твоя цель — дать легкий, изящный намек. 
        ЗАПРЕЩЕНО: называть соседей, части света, моря, горы, столицы, флаги или валюту.
        ИЗБЕГАЙ: очевидных фактов (типа 'родина пиццы' или 'страна кенгуру').
        ФОКУС: Этимология (происхождение названия), древние забытые законы, уникальные археологические находки или странные культурные традиции, которые косвенно указывают на регион.
        """
    else:
        logic = """
        Твоя цель — загадка для профи.
        ЗАПРЕЩЕНО: описывать вкус, ароматы (фрукты, кожа, бензол), цвет или называть регионы-лидеры.
        ФОКУС: Генеалогия лозы (кто 'родители'), форма листа на языке ботаников, исторические курьезы (например, как сорт перевозили контрабандой или как его называли 500 лет назад).
        """

    prompt = f"""
    Мы играем в винное казино. Дай ОДНУ нетривиальную и неочевидную подсказку про {target_type} '{target_value}'. 
    ID запроса: {seed}
    
    {logic}
    
    ПРАВИЛА ИСПОЛНЕНИЯ:
    1. КАТЕГОРИЧЕСКИ НЕ НАЗЫВАЙ '{target_value}'.
    2. Пиши изысканно, 2-3 законченных предложения. 
    3. Не используй вводные слова ("Вот ваш факт", "Интересно, что..."). Сразу к сути.
    4. Если не знаешь редкого факта, лучше напиши про геологический возраст почв или древнее название местности.
    5. ОБЯЗАТЕЛЬНО закончи мысль точкой.
    """
    
    try:
        safety = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
        
        response = model.generate_content(
            prompt, 
            generation_config=genai.types.GenerationConfig(
                temperature=1.0,
                max_output_tokens=1500,
                top_p=0.95
            ),
            safety_settings=safety
        )
        
        res = response.text.strip().replace('"', '')
        
        stop_symbols = ('.', '!', '?', '»', '—')
        if not res.endswith(stop_symbols):
            last_dot = max(res.rfind('.'), res.rfind('!'), res.rfind('?'))
            if last_dot != -1:
                res = res[:last_dot + 1]
            else:
                return "ИИ задумался о вечном. Нажмите кнопку еще раз для новой подсказки."
        
        return res
    except Exception as e:
        return f"Техническая заминка: {str(e)}"

# --- 3. УПРАВЛЕНИЕ СОСТОЯНИЕМ ---
state_keys = {
    "players": [], "page": "registration", "round_num": 1,
    "current_wine": {}, "bet_rows_count": 1,
    "hints": {"country": "", "grape": ""}, "current_player_idx": 0,
    "last_country": "—", "last_grape": "—"
}
for key, default in state_keys.items():
    if key not in st.session_state:
        st.session_state[key] = default

def header(show_logo=False):
    if show_logo:
        c1, c2, c3 = st.columns([1, 1.5, 1])
        with c2:
            try: st.image("logo.png", width=250)
            except: st.write("### WINE & WHISKEY")
    st.markdown("---")

# --- 4. СТРАНИЦЫ ---

def show_registration():
    header(show_logo=True)
    st.markdown("<h2 style='text-align: center;'>📝 Регистрация</h2>", unsafe_allow_html=True)
    
    # Используем форму (st.form), это железобетонно решает проблему двойного срабатывания в Streamlit
    with st.form("registration_form", clear_on_submit=True):
        name = st.text_input("Имя игрока:", placeholder="Введите имя и нажмите Enter или кнопку снизу")
        submitted = st.form_submit_button("Добавить игрока", use_container_width=True)
        
        if submitted and name.strip():
            st.session_state.players.append({
                "name": name.strip(), 
                "balance": 150, 
                "round_bets": [], 
                "balance_at_start": 150
            })
            st.rerun()
            
    if st.session_state.players:
        st.write("### Список гостей:")
        for p in st.session_state.players: 
            st.write(f"✅ {p['name']}")
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Начать игру ➔", use_container_width=True, type="primary"):
            st.session_state.page = "setup"
            st.rerun()

def show_setup():
    header(show_logo=False)
    st.markdown(f"### 🍷 Раунд №{st.session_state.round_num}")
    
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.markdown("#### Параметры вина")
        for cat, opts in DATA.items():
            st.session_state.current_wine[cat] = st.selectbox(f"{cat}:", ["—"] + opts, key=f"s_{cat}")
            
    current_country = st.session_state.current_wine.get("Страна", "—")
    current_grape = st.session_state.current_wine.get("Сорт винограда", "—")
    
    if current_country != "—" and current_country != st.session_state.last_country:
        st.session_state.hints["country"] = get_ai_hint("страну", current_country)
        st.session_state.last_country = current_country
        
    if current_grape != "—" and current_grape != st.session_state.last_grape:
        st.session_state.hints["grape"] = get_ai_hint("сорт винограда", current_grape)
        st.session_state.last_grape = current_grape

    with col2:
        st.markdown("#### Подсказки Сомелье-ИИ")
        
        if current_country != "—":
            st.info(st.session_state.hints["country"] or "Генерация подсказки...")
            if st.button("🔄 Обновить факт о Стране"):
                st.session_state.hints["country"] = get_ai_hint("страну", current_country)
                st.rerun()
        else:
            st.caption("Выберите страну для получения намёка.")
            
        st.markdown("<br>", unsafe_allow_html=True)
            
        if current_grape != "—":
            st.success(st.session_state.hints["grape"] or "Генерация подсказки...")
            if st.button("🔄 Обновить факт о Сорте"):
                st.session_state.hints["grape"] = get_ai_hint("сорт винограда", current_grape)
                st.rerun()
        else:
            st.caption("Выберите сорт винограда для получения намёка.")

    st.markdown("---")
    if st.button("Перейти к ставкам ➔", use_container_width=True, type="primary"):
        for p in st.session_state.players: p['balance_at_start'] = p['balance']
        st.session_state.page = "betting"
        st.session_state.current_player_idx = 0
        st.session_state.bet_rows_count = 1
        st.rerun()

def show_betting():
    header(show_logo=False)
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
        with c3: st.number_input("Сумма", min_value=0, step=10, key=f"p{p_idx}_a{i}")
        
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
    header(show_logo=False)
    correct = st.session_state.current_wine
    st.markdown("<h2 style='text-align: center;'>📊 Итоги Раунда</h2>", unsafe_allow_html=True)
    st.info("🎯 **Правильный ответ:** " + " | ".join([f"{k}: {v}" for k, v in correct.items() if v != "—"]))
    
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
            st.write(f"**До раунда:** {p['balance_at_start']} | **Итоговый баланс:** {p['balance']}")

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    if c1.button("Следующий раунд 🍷", use_container_width=True):
        st.session_state.round_num += 1
        st.session_state.page = "setup"
        st.session_state.hints = {"country": "", "grape": ""}
        st.session_state.last_country = "—"
        st.session_state.last_grape = "—"
        for k in list(st.session_state.keys()):
            if any(x in k for x in ["_v", "_a", "_c"]): del st.session_state[k]
        st.rerun()
        
    if c2.button("Завершить игру 🏆", use_container_width=True, type="primary"):
        st.session_state.page = "final"
        st.rerun()

def show_final():
    header(show_logo=False)
    st.markdown("<h1 style='text-align: center;'>🏆 Финал Игры</h1>", unsafe_allow_html=True)
    
    sorted_players = sorted(st.session_state.players, key=lambda x: x['balance'], reverse=True)
    for i, p in enumerate(sorted_players):
        if i == 0:
            st.success(f"🥇 1. {p['name']} — {p['balance']} фишек")
        elif i == 1:
            st.info(f"🥈 2. {p['name']} — {p['balance']} фишек")
        elif i == 2:
            st.warning(f"🥉 3. {p['name']} — {p['balance']} фишек")
        else:
            st.write(f"**{i+1}. {p['name']}** — {p['balance']} фишек")
            
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
