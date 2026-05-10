import streamlit as st
import google.generativeai as genai

# --- КОНФИГУРАЦИЯ ДАННЫХ ---
DATA = {
    "Сладость": ["сухое", "полусухое", "полусладкое", "сладкое"],
    "Страна": ["Россия", "ЮАР", "Австралия", "Аргентина", "США", "Новая Зеландия", "Чили", "Франция", "Италия", "Испания", "Австрия", "Германия", "Португалия", "Грузия", "Армения"],
    "Сорт винограда": ["Шардоне", "Рислинг", "Совиньон Блан", "Пино Гриджио", "Гевюрцтраминер", "Кортезе", "Гарганега", "Альбариньо", "Вердехо", "Грюнер Вельтлинер", "Каберне Совиньон", "Мерло", "Пино Нуар", "Сира/Шираз", "Темпранильо", "Санджовезе", "Мальбек", "Красностоп", "Саперави"],
    "Выдержка": ["выдержано в дубе", "не выдержано в дубе", "выдержано на осадке"],
    "Градус": ["11%", "12%", "13%", "14%"],
    "Год урожая": [str(year) for year in range(2015, 2027)]
}

COEFFS = {"Сладость": 2, "Выдержка": 2, "Страна": 3, "Сорт винограда": 3, "Градус": 4, "Год урожая": 5}

# --- НАСТРОЙКА ИИ ---
# Пытаемся взять ключ из Secrets или из кода (для локального теста)
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
except:
    model = None

def get_ai_hint(target_type, target_value):
    if not model:
        return "Ошибка: API ключ не настроен."
    
    prompt = f"""
    Ты эксперт-сомелье. Мы играем в винное казино. 
    Дай короткую (2-3 предложения) подсказку для игроков про {target_type}: {target_value}.
    ПРАВИЛА:
    1. НЕ НАЗЫВАЙ само слово '{target_value}'.
    2. НЕ используй слишком очевидные факты (например, про сапог для Италии или кенгуру для Австралии).
    3. Используй проф. термины: ароматика (бензол, косточковые, кожа), климат, терруар или исторические факты.
    4. Подсказка должна быть элегантной и заставлять подумать.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Не удалось получить подсказку: {str(e)}"

# --- ИНТЕРФЕЙС ---
st.set_page_config(page_title="WINE & WHISKEY Casino", page_icon="🍷")

if "players" not in st.session_state: st.session_state.players = []
if "page" not in st.session_state: st.session_state.page = "registration"
if "round_num" not in st.session_state: st.session_state.round_num = 1
if "hints" not in st.session_state: st.session_state.hints = {"country": "", "grape": ""}

def header():
    cols = st.columns([1, 2, 1])
    with cols[1]:
        try: st.image("logo.png", width=300)
        except: st.write("### WINE & WHISKEY")
    st.markdown("---")

def add_player():
    name = st.session_state.temp_name.strip()
    if name:
        st.session_state.players.append({"name": name, "balance": 1000, "round_bets": []})
        st.session_state.temp_name = ""

# --- СТРАНИЦЫ ---

def show_registration():
    header()
    st.markdown("<h2 style='text-align: center;'>📝 Регистрация</h2>", unsafe_allow_html=True)
    st.text_input("Имя игрока:", key="temp_name", on_change=add_player)
    if st.session_state.players:
        for p in st.session_state.players: st.write(f"✅ {p['name']}")
        if st.button("Начать ➔", use_container_width=True, type="primary"):
            st.session_state.page = "setup"
            st.rerun()

def show_setup():
    header()
    st.markdown(f"<h2 style='text-align: center;'>🍷 Настройка Раунда №{st.session_state.round_num}</h2>", unsafe_allow_html=True)
    
    temp_wine = {}
    with st.expander("Параметры вина", expanded=True):
        for cat, opts in DATA.items():
            temp_wine[cat] = st.selectbox(f"{cat}:", ["—"] + opts, key=f"s_{cat}")
    
    st.markdown("### 💡 Генератор подсказок")
    c1, c2 = st.columns(2)
    
    # Кнопка подсказки по стране
    if c1.button("🤖 Подсказать по Стране"):
        if temp_wine["Страна"] != "—":
            with st.spinner("ИИ подбирает слова..."):
                st.session_state.hints["country"] = get_ai_hint("страну", temp_wine["Страна"])
        else:
            st.warning("Сначала выберите страну!")

    # Кнопка подсказки по сорту
    if c2.button("🤖 Подсказать по Сорту"):
        if temp_wine["Сорт винограда"] != "—":
            with st.spinner("ИИ анализирует сорт..."):
                st.session_state.hints["grape"] = get_ai_hint("сорт винограда", temp_wine["Сорт винограда"])
        else:
            st.warning("Сначала выберите сорт!")

    # Вывод подсказок, если они сгенерированы
    if st.session_state.hints["country"]:
        st.info(f"**Намек на страну:**\n\n{st.session_state.hints['country']}")
    if st.session_state.hints["grape"]:
        st.success(f"**Намек на сорт:**\n\n{st.session_state.hints['grape']}")

    if st.button("К ставкам ➔", use_container_width=True, type="primary"):
        st.session_state.current_wine = temp_wine
        for p in st.session_state.players: p['balance_at_start'] = p['balance']
        st.session_state.page = "betting"
        st.session_state.current_player_idx = 0
        st.session_state.bet_rows_count = 1
        st.session_state.hints = {"country": "", "grape": ""} # Сброс подсказок для нового раунда
        st.rerun()

# --- (Остальные функции: show_betting, show_results, show_final остаются такими же, как в прошлом коде) ---
# ... (вставь сюда функции ставок и итогов из предыдущего сообщения) ...

# Запуск навигации
page = st.session_state.page
if page == "registration": show_registration()
elif page == "setup": show_setup()
elif page == "betting": # (вызов функции ставок)
    pass 
# и так далее...
