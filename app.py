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

st.set_page_config(page_title="Винное Казино", page_icon="🍷")

# Инициализация данных в памяти браузера
if "players" not in st.session_state:
    st.session_state.players = []
if "round_num" not in st.session_state:
    st.session_state.round_num = 1
if "page" not in st.session_state:
    st.session_state.page = "registration"
if "current_wine" not in st.session_state:
    st.session_state.current_wine = {}

# --- ЛОГИКА СТРАНИЦ ---

def show_registration():
    st.title("🍷 Регистрация участников")
    
    with st.form("reg_form", clear_on_submit=True):
        new_name = st.text_input("Имя игрока:")
        add_btn = st.form_submit_button("Добавить")
        if add_btn and new_name:
            st.session_state.players.append({"name": new_name, "balance": 1000, "round_bets": []})
    
    if st.session_state.players:
        st.write("### Список игроков:")
        for p in st.session_state.players:
            st.write(f"- {p['name']} (1000 фишек)")
        
        if st.button("Завершить регистрацию и начать"):
            st.session_state.page = "setup"
            st.rerun()

def show_setup():
    st.title(f"🍇 Раунд №{st.session_state.round_num}")
    st.subheader("Настройка вина (можно пропустить поля)")
    
    with st.form("setup_form"):
        temp_wine = {}
        cols = st.columns(2)
        for i, (cat, opts) in enumerate(DATA.items()):
            with cols[i % 2]:
                temp_wine[cat] = st.selectbox(cat, ["—"] + opts)
        
        if st.form_submit_button("Принять ставки"):
            st.session_state.current_wine = temp_wine
            st.session_state.page = "betting"
            st.session_state.current_player_idx = 0
            st.rerun()

def show_betting():
    idx = st.session_state.current_player_idx
    player = st.session_state.players[idx]
    
    st.title(f"👤 Ставки: {player['name']}")
    st.info(f"Баланс: {player['balance']} фишек")
    
    # Создаем 5 строк для ставок (можно расширить)
    player_bets = []
    with st.form(f"bet_form_{idx}"):
        for i in range(5):
            c1, c2, c3 = st.columns([2, 2, 1])
            cat = c1.selectbox(f"Тип {i+1}", list(COEFFS.keys()), key=f"cat_{idx}_{i}")
            val = c2.selectbox(f"Вариант {i+1}", ["—"] + DATA[cat], key=f"val_{idx}_{i}")
            amt = c3.number_input(f"Фишки", min_value=0, step=5, key=f"amt_{idx}_{i}")
            if val != "—" and amt > 0:
                player_bets.append({"cat": cat, "val": val, "amt": amt})
        
        if st.form_submit_button("Подтвердить ставки"):
            total_spent = sum(b['amt'] for b in player_bets)
            if total_spent > player['balance']:
                st.error("Недостаточно фишек!")
            else:
                player['round_bets'] = player_bets
                player['balance'] -= total_spent
                player['last_spent'] = total_spent
                
                if st.session_state.current_player_idx < len(st.session_state.players) - 1:
                    st.session_state.current_player_idx += 1
                else:
                    st.session_state.page = "results"
                st.rerun()

def show_results():
    st.title(f"📊 Итоги раунда №{st.session_state.round_num}")
    
    # Показываем правильные ответы
    st.success("Правильное вино: " + ", ".join([f"{k}: {v}" for k, v in st.session_state.current_wine.items() if v != "—"]))
    
    for p in st.session_state.players:
        win_sum = 0
        for b in p['round_bets']:
            if b['val'] == st.session_state.current_wine.get(b['cat']):
                win_sum += b['amt'] * COEFFS[b['cat']]
        
        old_bal = p['balance']
        p['balance'] += win_sum
        st.write(f"**{p['name']}**: {old_bal} ➔ {p['balance']} (Выдать: **{win_sum}** фишек)")
    
    c1, c2 = st.columns(2)
    if c1.button("Следующий раунд"):
        st.session_state.round_num += 1
        st.session_state.page = "setup"
        st.rerun()
    if c2.button("Завершить игру"):
        st.session_state.page = "final"
        st.rerun()

def show_final():
    st.title("🏆 Финал")
    sorted_p = sorted(st.session_state.players, key=lambda x: x['balance'], reverse=True)
    for i, p in enumerate(sorted_p):
        st.subheader(f"{i+1}. {p['name']} — {p['balance']} фишек")
    
    if st.button("Новая игра"):
        st.session_state.clear()
        st.rerun()

# Навигатор
if st.session_state.page == "registration": show_registration()
elif st.session_state.page == "setup": show_setup()
elif st.session_state.page == "betting": show_betting()
elif st.session_state.page == "results": show_results()
elif st.session_state.page == "final": show_final()