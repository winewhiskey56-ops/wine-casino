import streamlit as st

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

st.set_page_config(page_title="WINE & WHISKEY Casino", page_icon="🍷", layout="centered")

# Инициализация состояний
if "players" not in st.session_state: st.session_state.players = []
if "round_num" not in st.session_state: st.session_state.round_num = 1
if "page" not in st.session_state: st.session_state.page = "registration"
if "current_wine" not in st.session_state: st.session_state.current_wine = {}
if "bet_rows_count" not in st.session_state: st.session_state.bet_rows_count = 1

def header():
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.warning("Файл logo.png не найден.")
    st.markdown("---")

def add_player():
    name = st.session_state.temp_name.strip()
    if name:
        st.session_state.players.append({
            "name": name, 
            "balance": 1000, 
            "round_bets": [],
            "balance_before_round": 1000
        })
        st.session_state.temp_name = "" # Очистка поля

# --- СТРАНИЦЫ ---

def show_registration():
    header()
    st.markdown("<h2 style='text-align: center;'>📝 Регистрация участников</h2>", unsafe_allow_html=True)
    
    st.text_input("Имя игрока:", key="temp_name", on_change=add_player, placeholder="Введите имя и нажмите Enter")
    
    if st.button("Добавить в список", use_container_width=True):
        add_player()

    if st.session_state.players:
        st.markdown("### Текущий состав:")
        for i, p in enumerate(st.session_state.players):
            st.markdown(f"**{i+1}. {p['name']}** — {p['balance']} фишек")
        
        if st.button("Начать игру ➔", use_container_width=True, type="primary"):
            st.session_state.page = "setup"
            st.rerun()

def show_setup():
    header()
    st.markdown(f"<h2 style='text-align: center;'>🍇 Раунд №{st.session_state.round_num}</h2>", unsafe_allow_html=True)
    
    temp_wine = {}
    with st.expander("Настройка вина", expanded=True):
        for cat, opts in DATA.items():
            temp_wine[cat] = st.selectbox(f"{cat}:", ["—"] + opts, key=f"setup_{cat}")
    
    if st.button("Принять настройки ➔", use_container_width=True, type="primary"):
        st.session_state.current_wine = temp_wine
        # Сохраняем баланс игроков перед началом ставок раунда
        for p in st.session_state.players:
            p['balance_before_round'] = p['balance']
        st.session_state.page = "betting"
        st.session_state.current_player_idx = 0
        st.session_state.bet_rows_count = 1
        st.rerun()

def show_betting():
    header()
    player = st.session_state.players[st.session_state.current_player_idx]
    st.markdown(f"<h2 style='text-align: center;'>👤 Игрок: {player['name']}</h2>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center;'>Доступно: {player['balance']} фишек</h4>", unsafe_allow_html=True)
    
    current_bets = []
    total_spent = 0
    
    for i in range(st.session_state.bet_rows_count):
        cols = st.columns([2, 2, 1])
        cat = cols[0].selectbox(f"Тип {i+1}", list(COEFFS.keys()), key=f"p{idx}_c{i}")
        val = cols[1].selectbox(f"Вариант {i+1}", ["—"] + DATA[cat], key=f"p{idx}_v{i}")
        amt = cols[2].number_input(f"Фишки", min_value=0, step=50, key=f"p{idx}_a{i}")
        
        if val != "—" and amt > 0:
            current_bets.append({"cat": cat, "val": val, "amt": amt})
            total_spent += amt
            if i == st.session_state.bet_rows_count - 1:
                st.session_state.bet_rows_count += 1
                st.rerun()

    if st.button("Зарегистрировать ставки ➔", use_container_width=True, type="primary"):
        if total_spent > player['balance']:
            st.error("Недостаточно фишек!")
        else:
            player['round_bets'] = current_bets
            player['balance'] -= total_spent
            if st.session_state.current_player_idx < len(st.session_state.players) - 1:
                st.session_state.current_player_idx += 1
                st.session_state.bet_rows_count = 1
            else:
                st.session_state.page = "results"
            st.rerun()

def show_results():
    header()
    st.markdown(f"<h2 style='text-align: center;'>📊 Итоги раунда №{st.session_state.round_num}</h2>", unsafe_allow_html=True)
    st.info("🎯 **Правильное вино:** " + " | ".join([f"{k}: {v}" for k, v in st.session_state.current_wine.items() if v != "—"]))
    
    for p in st.session_state.players:
        win_sum = 0
        history_html = ""
        
        for b in p['round_bets']:
            correct = st.session_state.current_wine.get(b['cat'])
            is_win = str(b['val']).lower() == str(correct).lower()
            
            if is_win:
                prize = b['amt'] * COEFFS[b['cat']]
                win_sum += prize
                history_html += f"<p style='color:green; margin:0;'>✅ {b['cat']}: {b['val']} | {b['amt']} ➔ {prize}</p>"
            else:
                history_html += f"<p style='color:red; margin:0;'>❌ {b['cat']}: {b['val']} | {b['amt']} ➔ 0</p>"
        
        p['balance'] += win_sum
        
        with st.expander(f"👤 {p['name']} | Выдать: {win_sum} фишек"):
            st.markdown(history_html or "Ставок не было", unsafe_allow_html=True)
            st.markdown("---")
            st.write(f"🔹 Было в начале раунда: {p['balance_before_round']}")
            st.write(f"🔹 Стало в конце раунда: {p['balance']}")
            st.markdown(f"**ИТОГОВАЯ ВЫДАЧА: {win_sum}**")

    c1, c2 = st.columns(2)
    if c1.button("Следующий раунд 🍷", use_container_width=True):
        st.session_state.round_num += 1
        st.session_state.page = "setup"
        st.rerun()
    if c2.button("Завершить игру 🏆", use_container_width=True):
        st.session_state.page = "final"
        st.rerun()

def show_final():
    header()
    st.markdown("<h1 style='text-align: center;'>🏆 Победители</h1>", unsafe_allow_html=True)
    sorted_p = sorted(st.session_state.players, key=lambda x: x['balance'], reverse=True)
    for i, p in enumerate(sorted_p):
        st.subheader(f"{['🥇','🥈','🥉'][i] if i<3 else '👤'} {p['name']}: {p['balance']} фишек")
    if st.button("Новая игра", use_container_width=True):
        st.session_state.clear()
        st.rerun()

idx = st.session_state.get('current_player_idx', 0)
if st.session_state.page == "registration": show_registration()
elif st.session_state.page == "setup": show_setup()
elif st.session_state.page == "betting": show_betting()
elif st.session_state.page == "results": show_results()
elif st.session_state.page == "final": show_final()
