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

# --- НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(page_title="WINE & WHISKEY Casino", page_icon="🍷", layout="centered")

# Инициализация состояний
if "players" not in st.session_state: st.session_state.players = []
if "round_num" not in st.session_state: st.session_state.round_num = 1
if "page" not in st.session_state: st.session_state.page = "registration"
if "current_wine" not in st.session_state: st.session_state.current_wine = {}
if "bet_rows_count" not in st.session_state: st.session_state.bet_rows_count = 1

def header():
    # Отображение логотипа
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.warning("Файл logo.png не найден. Поместите его в папку с программой.")
    st.markdown("---")

# --- СТРАНИЦЫ ---

def show_registration():
    header()
    st.markdown("<h2 style='text-align: center;'>📝 Регистрация участников</h2>", unsafe_allow_html=True)
    
    with st.container():
        new_name = st.text_input("Имя игрока:", placeholder="Введите имя и нажмите Enter", key="reg_input")
        if st.button("Добавить в список") or (new_name and st.session_state.get('last_name') != new_name):
            if new_name:
                st.session_state.players.append({"name": new_name, "balance": 1000, "round_bets": []})
                st.session_state.last_name = new_name
                st.rerun()

    if st.session_state.players:
        st.markdown("### Текущий состав:")
        for i, p in enumerate(st.session_state.players):
            st.markdown(f"**{i+1}. {p['name']}** — 1000 фишек")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Начать игру ➔", use_container_width=True, type="primary"):
            st.session_state.page = "setup"
            st.rerun()

def show_setup():
    header()
    st.markdown(f"<h2 style='text-align: center;'>🍇 Раунд №{st.session_state.round_num}</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Настройте параметры дегустационного вина</p>", unsafe_allow_html=True)
    
    temp_wine = {}
    with st.expander("Открыть настройки вина", expanded=True):
        for cat, opts in DATA.items():
            temp_wine[cat] = st.selectbox(f"Выберите {cat}:", ["—"] + opts, key=f"setup_{cat}")
    
    if st.button("Принять настройки и перейти к ставкам ➔", use_container_width=True, type="primary"):
        st.session_state.current_wine = temp_wine
        st.session_state.page = "betting"
        st.session_state.current_player_idx = 0
        st.session_state.bet_rows_count = 1
        st.rerun()

def show_betting():
    header()
    player = st.session_state.players[st.session_state.current_player_idx]
    
    st.markdown(f"<h2 style='text-align: center;'>👤 Игрок: {player['name']}</h2>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center; color: #888;'>Ваш баланс: {player['balance']} фишек</h4>", unsafe_allow_html=True)
    
    current_bets = []
    total_spent = 0
    
    # Динамическое отображение строк ставок
    for i in range(st.session_state.bet_rows_count):
        with st.container():
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                cat = st.selectbox(f"Тип {i+1}", list(COEFFS.keys()), key=f"p{player['name']}_cat_{i}")
            with c2:
                val = st.selectbox(f"Вариант {i+1}", ["—"] + DATA[cat], key=f"p{player['name']}_val_{i}")
            with c3:
                amt = st.number_input(f"Фишки", min_value=0, step=50, key=f"p{player['name']}_amt_{i}")
            
            if val != "—" and amt > 0:
                current_bets.append({"cat": cat, "val": val, "amt": amt})
                total_spent += amt
                # Если заполнена текущая последняя строка, увеличиваем счетчик для следующей
                if i == st.session_state.bet_rows_count - 1:
                    st.session_state.bet_rows_count += 1
                    st.rerun()

    st.markdown("---")
    st.markdown(f"**Итоговая сумма ставок: {total_spent}**")
    
    if st.button("Зарегистрировать ставки ➔", use_container_width=True, type="primary"):
        if total_spent > player['balance']:
            st.error("Недостаточно фишек для таких ставок!")
        elif total_spent == 0:
            st.warning("Сделайте хотя бы одну ставку.")
        else:
            player['round_bets'] = current_bets
            player['balance'] -= total_spent
            
            if st.session_state.current_player_idx < len(st.session_state.players) - 1:
                st.session_state.current_player_idx += 1
                st.session_state.bet_rows_count = 1
                st.rerun()
            else:
                st.session_state.page = "results"
                st.rerun()

def show_results():
    header()
    st.markdown(f"<h2 style='text-align: center;'>📊 Итоги раунда №{st.session_state.round_num}</h2>", unsafe_allow_html=True)
    
    # Красивая карточка правильных ответов
    st.info("🎯 **Правильные характеристики:**\n\n" + 
            " | ".join([f"**{k}**: {v}" for k, v in st.session_state.current_wine.items() if v != "—"]))
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    for p in st.session_state.players:
        win_sum = 0
        for b in p['round_bets']:
            if str(b['val']).lower() == str(st.session_state.current_wine.get(b['cat'])).lower():
                win_sum += b['amt'] * COEFFS[b['cat']]
        
        p['balance'] += win_sum
        
        with st.expander(f"👤 {p['name']} | Выигрыш: {win_sum} фишек"):
            st.write(f"Текущий баланс: **{p['balance']}**")
            st.markdown(f"<p style='color: green;'>Необходимо выдать: <b>{win_sum}</b> фишек</p>", unsafe_allow_html=True)

    st.markdown("---")
    c1, c2 = st.columns(2)
    if c1.button("Следующий раунд 🍷"):
        st.session_state.round_num += 1
        st.session_state.page = "setup"
        st.rerun()
    if c2.button("Завершить игру 🏆"):
        st.session_state.page = "final"
        st.rerun()

def show_final():
    header()
    st.markdown("<h1 style='text-align: center;'>🏆 Финальный зачет</h1>", unsafe_allow_html=True)
    
    sorted_p = sorted(st.session_state.players, key=lambda x: x['balance'], reverse=True)
    
    for i, p in enumerate(sorted_p):
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "👤"
        st.markdown(f"### {medal} {p['name']} — **{p['balance']}** фишек")
    
    if st.button("Начать новую игру"):
        st.session_state.clear()
        st.rerun()

# Навигация
if st.session_state.page == "registration": show_registration()
elif st.session_state.page == "setup": show_setup()
elif st.session_state.page == "betting": show_betting()
elif st.session_state.page == "results": show_results()
elif st.session_state.page == "final": show_final()