import streamlit as st

# --- КОНФИГУРАЦИЯ ---
DATA = {
    "Сладость": ["сухое", "полусухое", "полусладкое", "сладкое"],
    "Страна": ["Россия", "ЮАР", "Австралия", "Аргентина", "США", "Новая Зеландия", "Чили", "Франция", "Италия", "Испания", "Австрия", "Германия", "Португалия", "Грузия", "Армения"],
    "Сорт винограда": ["Шардоне", "Рислинг", "Совиньон Блан", "Пино Гриджио", "Гевюрцтраминер", "Кортезе", "Гарганега", "Альбариньо", "Вердехо", "Грюнер Вельтлинер", "Каберне Совиньон", "Мерло", "Пино Нуар", "Сира/Шираз", "Темпранильо", "Санджовезе", "Мальбек", "Красностоп", "Саперави"],
    "Выдержка": ["выдержано в дубе", "не выдержано в дубе", "выдержано на осадке"],
    "Градус": ["11%", "12%", "13%", "14%"],
    "Год урожая": [str(year) for year in range(2015, 2027)]
}

COEFFS = {"Сладость": 2, "Выдержка": 2, "Страна": 3, "Сорт винограда": 3, "Градус": 4, "Год урожая": 5}

st.set_page_config(page_title="WINE & WHISKEY Casino", page_icon="🍷", layout="centered")

# Инициализация
if "players" not in st.session_state: st.session_state.players = []
if "round_num" not in st.session_state: st.session_state.round_num = 1
if "page" not in st.session_state: st.session_state.page = "registration"
if "current_wine" not in st.session_state: st.session_state.current_wine = {}
if "bet_rows_count" not in st.session_state: st.session_state.bet_rows_count = 1

def header():
    cols = st.columns([1, 2, 1]) # Центрируем логотип и делаем его меньше
    with cols[1]:
        try:
            st.image("logo.png", width=300) # Фиксированная ширина для аккуратности
        except:
            st.write("### WINE & WHISKEY")
    st.markdown("---")

def add_player():
    name = st.session_state.temp_name.strip()
    if name:
        st.session_state.players.append({
            "name": name, 
            "balance": 1000, 
            "round_bets": [],
            "balance_at_start": 1000
        })
        st.session_state.temp_name = ""

# --- ЛОГИКА СТРАНИЦ ---

def show_registration():
    header()
    st.markdown("<h2 style='text-align: center;'>📝 Регистрация</h2>", unsafe_allow_html=True)
    st.text_input("Имя игрока:", key="temp_name", on_change=add_player)
    
    if st.session_state.players:
        for p in st.session_state.players:
            st.write(f"✅ {p['name']} (1000)")
        if st.button("Начать игру ➔", use_container_width=True, type="primary"):
            st.session_state.page = "setup"
            st.rerun()

def show_setup():
    header()
    st.markdown(f"<h2 style='text-align: center;'>🍷 Раунд №{st.session_state.round_num}</h2>", unsafe_allow_html=True)
    
    temp_wine = {}
    with st.expander("Характеристики вина (для крупье)", expanded=True):
        for cat, opts in DATA.items():
            temp_wine[cat] = st.selectbox(f"{cat}:", ["—"] + opts, key=f"s_{cat}")
    
    if st.button("К ставкам ➔", use_container_width=True, type="primary"):
        st.session_state.current_wine = temp_wine
        for p in st.session_state.players:
            p['balance_at_start'] = p['balance']
        st.session_state.page = "betting"
        st.session_state.current_player_idx = 0
        st.session_state.bet_rows_count = 1
        st.rerun()

def show_betting():
    header()
    player = st.session_state.players[st.session_state.current_player_idx]
    
    # Считаем текущие затраты ПЕРЕД отрисовкой, чтобы обновить баланс в реальном времени
    temp_spent = 0
    valid_bets = []
    for i in range(st.session_state.bet_rows_count):
        # Собираем данные из виджетов, если они уже существуют
        c_cat = st.session_state.get(f"b_cat_{i}")
        c_amt = st.session_state.get(f"b_amt_{i}", 0)
        c_val = st.session_state.get(f"b_val_{i}", "—")
        if c_val != "—" and c_amt > 0:
            temp_spent += c_amt
            valid_bets.append({"cat": c_cat, "val": c_val, "amt": c_amt})

    real_time_balance = player['balance'] - temp_spent
    
    st.markdown(f"<h2 style='text-align: center;'>👤 {player['name']}</h2>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; color: #D4AF37;'>Остаток: {real_time_balance}</h3>", unsafe_allow_html=True)
    
    # Отрисовка полей ставок
    for i in range(st.session_state.bet_rows_count):
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1: 
            cat = st.selectbox(f"Тип", list(COEFFS.keys()), key=f"b_cat_{i}")
        with c2: 
            val = st.selectbox(f"Вариант", ["—"] + DATA[cat], key=f"b_val_{i}")
        with c3: 
            amt = st.number_input(f"Сумма", min_value=0, step=50, key=f"b_amt_{i}")
            
        # Если последняя строка заполнена — добавляем новую
        if i == st.session_state.bet_rows_count - 1 and val != "—" and amt > 0:
            st.session_state.bet_rows_count += 1
            st.rerun()

    if st.button("Принять ставки ➔", use_container_width=True, type="primary"):
        if real_time_balance < 0:
            st.error("Превышен баланс!")
        elif not valid_bets:
            st.warning("Нет ставок")
        else:
            player['round_bets'] = valid_bets
            player['balance'] = real_time_balance # Вычитаем только реально поставленное
            
            if st.session_state.current_player_idx < len(st.session_state.players) - 1:
                st.session_state.current_player_idx += 1
                st.session_state.bet_rows_count = 1
                # Очищаем ключи виджетов для следующего игрока
                for key in list(st.session_state.keys()):
                    if key.startswith("b_"): del st.session_state[key]
            else:
                st.session_state.page = "results"
            st.rerun()

def show_results():
    header()
    st.markdown("<h2 style='text-align: center;'>📊 Итоги</h2>", unsafe_allow_html=True)
    
    # Правильное вино
    correct = st.session_state.current_wine
    st.info("🎯 Вино: " + " | ".join([f"{k}: {v}" for k, v in correct.items() if v != "—"]))
    
    for p in st.session_state.players:
        win_sum = 0
        details = []
        for b in p['round_bets']:
            is_hit = b['val'] == correct.get(b['cat'])
            res_amt = b['amt'] * COEFFS[b['cat']] if is_hit else 0
            win_sum += res_amt
            icon = "✅" if is_hit else "❌"
            color = "green" if is_hit else "red"
            details.append(f"<p style='color:{color}; margin:0;'>{icon} {b['cat']}: {b['val']} | {b['amt']} ➔ {res_amt}</p>")
        
        balance_after = p['balance'] + win_sum
        
        with st.expander(f"👤 {p['name']} | Выигрыш: +{win_sum}"):
            st.markdown("".join(details), unsafe_allow_html=True)
            st.markdown("---")
            st.write(f"💰 До раунда: {p['balance_at_start']}")
            st.write(f"💳 Итог раунда: {balance_after}")
            p['balance'] = balance_after # Сохраняем итоговый баланс

    if st.button("Следующий раунд 🍷", use_container_width=True):
        st.session_state.round_num += 1
        st.session_state.page = "setup"
        # Очистка ставок
        for p in st.session_state.players: p['round_bets'] = []
        st.rerun()
    
    if st.button("Завершить игру 🏆", use_container_width=True):
        st.session_state.page = "final"
        st.rerun()

def show_final():
    header()
    st.markdown("<h1 style='text-align: center;'>🏆 Финал</h1>", unsafe_allow_html=True)
    sorted_p = sorted(st.session_state.players, key=lambda x: x['balance'], reverse=True)
    for i, p in enumerate(sorted_p):
        st.subheader(f"{i+1}. {p['name']} — {p['balance']}")
    if st.button("Новая игра"):
        st.session_state.clear()
        st.rerun()

# Навигация
page = st.session_state.page
if page == "registration": show_registration()
elif page == "setup": show_setup()
elif page == "betting": show_betting()
elif page == "results": show_results()
elif page == "final": show_final()
