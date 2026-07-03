import streamlit as st
import random
import json
import os

BACKUP_FILE = "wine_casino_backup.json"

# --- ФУНКЦИИ ЗАЩИТЫ ОТ СБРОСА СЕССИИ ---
def save_game_state():
    state_to_save = {}
    for k in ["players", "page", "round_num", "current_wine", "bet_rows_count", "current_player_idx", "shuffle_players", "shuffle_order", "active_params", "init_balance", "coeffs"]:
        if k in st.session_state:
            state_to_save[k] = st.session_state[k]
    
    dynamic_keys = {k: st.session_state[k] for k in st.session_state.keys() if any(x in k for x in ["_v", "_a", "_c"])}
    state_to_save["dynamic_keys"] = dynamic_keys

    with open(BACKUP_FILE, "w", encoding="utf-8") as f:
        json.dump(state_to_save, f, ensure_ascii=False, indent=4)

def load_game_state():
    if os.path.exists(BACKUP_FILE):
        try:
            with open(BACKUP_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in data.items():
                    if k != "dynamic_keys":
                        st.session_state[k] = v
                if "dynamic_keys" in data:
                    for dk, dv in data["dynamic_keys"].items():
                        st.session_state[dk] = dv
        except:
            pass

def clear_game_backup():
    if os.path.exists(BACKUP_FILE):
        try: os.remove(BACKUP_FILE)
        except: pass

# Загрузка состояния при старте/обновлении страницы
load_game_state()

# --- БАЗОВАЯ КОНФИГУРАЦИЯ ВАРИАНТОВ ---
DATA = {
    "Сладость": ["сухое", "полусухое", "полусладкое", "сладкое"],
    "Страна": ["Россия", "Франция", "Италия", "Испания", "Германия", "Новая Зеландия", "Чили", "Аргентина", "ЮАР", "Австрия", "Португалия", "США", "Австралия", "Грузия", "Армения"],
    "Сорт винограда": ["Шардоне", "Совиньон Блан", "Рислинг", "Пино Гриджио", "Гевюрцтраминер", "Кортезе", "Альбариньо", "Вердехо", "Грюнер Вельтлинер", "Каберне Совиньон", "Мерло", "Пино Нуар", "Сира/Шираз", "Темпранильо", "Санджовезе", "Мальбек", "Красностоп", "Саперави"],
    "Выдержка": ["выдержано в дубе", "не выдержано в дубе", "выдержано на осадке"],
    "Год урожая": [],  
    "Процент алкоголя": []  
}

DEFAULT_COEFFS = {
    "Страна": 2, 
    "Сорт винограда": 3, 
    "Сладость": 2, 
    "Выдержка": 3,
    "Год урожая": 3,
    "Процент алкоголя": 2
}

# Инициализация дефолтных ключей сессии, если их нет
keys = ["players", "page", "round_num", "current_wine", "bet_rows_count", "current_player_idx", "shuffle_players", "shuffle_order", "active_params", "init_balance", "coeffs"]
defs = [[], "setup_params", 1, {}, 1, 0, False, [], list(DEFAULT_COEFFS.keys()), 150, DEFAULT_COEFFS.copy()]
for k, d in zip(keys, defs):
    if k not in st.session_state: st.session_state[k] = d

def header():
    st.write("### 🍷 WINE & WHISKEY")
    st.markdown("---")

# --- СТРАНИЦА 1: НАСТРОЙКА ИГРОВЫХ ПАРАМЕТРОВ ---
def show_setup_params():
    header()
    st.markdown("<h2 style='text-align: center;'>⚙️ 1. Настройка параметров игры</h2>", unsafe_allow_html=True)
    
    st.session_state.init_balance = st.number_input("Стартовый баланс фишек у игроков:", min_value=10, value=int(st.session_state.init_balance), step=10)
    
    st.markdown("### Выберите играемые параметры и коэффициент умножения:")
    
    chosen_params = []
    updated_coeffs = st.session_state.coeffs.copy()
    
    for param in list(DEFAULT_COEFFS.keys()):
        col_check, col_coeff = st.columns([4, 5])
        with col_check:
            st.write("") # Небольшой отступ для выравнивания с радио-кнопками
            is_active = st.checkbox(param, value=(param in st.session_state.active_params), key=f"check_{param}")
            if is_active:
                chosen_params.append(param)
        with col_coeff:
            current_coef = st.session_state.coeffs.get(param, DEFAULT_COEFFS[param])
            # Защита на случай, если старый коэффициент выпал за рамки [2, 3, 4, 5]
            if current_coef not in [2, 3, 4, 5]:
                current_coef = 2
            
            # Выбор точек радио-кнопками горизонтально
            selected_coef = st.radio(
                f"Коэффициент для: {param}",
                options=[2, 3, 4, 5],
                index=[2, 3, 4, 5].index(current_coef),
                horizontal=True,
                key=f"coef_radio_{param}"
            )
            updated_coeffs[param] = selected_coef
            
    st.session_state.active_params = chosen_params
    st.session_state.coeffs = updated_coeffs
    
    save_game_state()
    st.markdown("---")
    
    if st.button("Далее к регистрации участников ➔", use_container_width=True, type="primary"):
        if not st.session_state.active_params:
            st.error("Ошибка: выберите хотя бы один играемый параметр!")
        else:
            st.session_state.page = "registration"
            save_game_state()
            st.rerun()

# --- СТРАНИЦА 2: РЕГИСТРАЦИЯ УЧАСТНИКОВ ---
def show_registration():
    header()
    st.markdown("<h2 style='text-align: center;'>📝 2. Регистрация участников</h2>", unsafe_allow_html=True)
    
    with st.form("reg_form", clear_on_submit=True):
        name = st.text_input("Имя игрока:")
        if st.form_submit_button("Добавить", use_container_width=True) and name.strip():
            player_num = len(st.session_state.players) + 1
            st.session_state.players.append({
                "id": player_num,
                "name": name.strip(), 
                "balance": st.session_state.init_balance, 
                "round_bets": [], 
                "balance_at_start": st.session_state.init_balance
            })
            save_game_state()
            st.rerun()
            
    st.session_state.shuffle_players = st.checkbox(
        "🔀 Перемешивать участников случайным образом каждый раунд", 
        value=st.session_state.shuffle_players
    )
    
    if st.session_state.players:
        st.markdown("### Список гостей:")
        for p in st.session_state.players: 
            st.write(f"Игрок №{p['id']}: **{p['name']}** ({p['balance']} фишек)")
            
    st.markdown("---")
    col_nav1, col_nav2 = st.columns(2)
    
    if col_nav1.button("⬅️ Назад в параметры", use_container_width=True):
        st.session_state.page = "setup_params"
        st.rerun()
        
    if col_nav2.button("Начать игру ➔", use_container_width=True, type="primary"):
        if not st.session_state.players:
            st.error("Добавьте хотя бы одного игрока!")
            return
        st.session_state.page = "setup_wine"
        if st.session_state.shuffle_players:
            st.session_state.shuffle_order = random.sample(range(len(st.session_state.players)), len(st.session_state.players))
        else:
            st.session_state.shuffle_order = list(range(len(st.session_state.players)))
        save_game_state()
        st.rerun()

# --- СТРАНИЦА 3: ВВОД ПАРАМЕТРОВ ЗАГАДАННОГО ВИНА ---
def show_setup_wine():
    header()
    st.markdown(f"### 🍷 Раунд №{st.session_state.round_num}")
    st.markdown("#### Загадайте параметры скрытого образца:")
    
    c1, c2 = st.columns(2)
    
    if "Страна" in st.session_state.active_params:
        with c1:
            old_country = st.session_state.current_wine.get("Страna_raw", "—")
            options = ["—"] + DATA["Страна"] + ["📝 Свой вариант..."]
            country_select = st.selectbox("Страна:", options, index=options.index(old_country) if old_country in options else 0)
            st.session_state.current_wine["Страна"] = st.text_input("Введите страну вручную:", value=st.session_state.current_wine.get("Страна", "")).strip() if country_select == "📝 Свой вариант..." else country_select
            st.session_state.current_wine["Страna_raw"] = country_select

    if "Сорт винограда" in st.session_state.active_params:
        with c1:
            old_grape = st.session_state.current_wine.get("Сорт_raw", "—")
            options = ["—"] + DATA["Сорт винограда"] + ["📝 Свой вариант..."]
            grape_select = st.selectbox("Сорт винограда:", options, index=options.index(old_grape) if old_grape in options else 0)
            st.session_state.current_wine["Сорт винограда"] = st.text_input("Введите сорт вручную:", value=st.session_state.current_wine.get("Сорт винограда", "")).strip() if grape_select == "📝 Свой вариант..." else grape_select
            st.session_state.current_wine["Сорт_raw"] = grape_select

    if "Сладость" in st.session_state.active_params:
        with c2:
            st.session_state.current_wine["Сладость"] = st.selectbox("Сладость:", ["—"] + DATA["Сладость"], index=(["—"] + DATA["Сладость"]).index(st.session_state.current_wine.get("Сладость", "—")) if st.session_state.current_wine.get("Сладость") in (["—"] + DATA["Сладость"]) else 0)

    if "Выдержка" in st.session_state.active_params:
        with c2:
            st.session_state.current_wine["Выдержка"] = st.selectbox("Выдержка:", ["—"] + DATA["Выдержка"], index=(["—"] + DATA["Выдержка"]).index(st.session_state.current_wine.get("Выдержка", "—")) if st.session_state.current_wine.get("Выдержка") in (["—"] + DATA["Выдержка"]) else 0)
            
    if "Год урожая" in st.session_state.active_params:
        with c1:
            st.session_state.current_wine["Год урожая"] = st.number_input("Год урожая (эталон):", min_value=1800, max_value=2026, value=int(st.session_state.current_wine.get("Год урожая", 2020)), step=1)

    if "Процент алкоголя" in st.session_state.active_params:
        with c2:
            st.session_state.current_wine["Процент алкоголя"] = st.number_input("Процент алкоголя (эталон %):", min_value=0.0, max_value=25.0, value=float(st.session_state.current_wine.get("Процент алкоголя", 12.5)), step=0.1)
            st.caption("ℹ️ Напоминание: выигрывают ставки с погрешностью ±0.5%")
        
    save_game_state()
    st.markdown("---")
    
    col_b1, col_b2 = st.columns(2)
    if col_b1.button("⬅️ Назад к регистрации", use_container_width=True):
        st.session_state.page = "registration"
        st.rerun()
        
    if col_b2.button("К ставкам ➔", use_container_width=True, type="primary"):
        for p in st.session_state.players: 
            p['balance_at_start'] = p['balance']
        st.session_state.page = "betting"
        st.session_state.current_player_idx = 0
        st.session_state.bet_rows_count = 1
        save_game_state()
        st.rerun()

# --- СТРАНИЦА 4: ПООЧЕРЕДНЫЙ ПРИЕМ СТАВОК ---
def show_betting():
    header()
    
    current_seat_idx = st.session_state.shuffle_order[st.session_state.current_player_idx]
    player = st.session_state.players[current_seat_idx]
    p_idx = current_seat_idx 
    
    spent, valid = 0, []
    for i in range(st.session_state.bet_rows_count):
        cat = st.session_state.get(f"p{p_idx}_c{i}", st.session_state.active_params[0])
        val = st.session_state.get(f"p{p_idx}_v{i}", "—")
        amt = st.session_state.get(f"p{p_idx}_a{i}", 0)
        if val != "—" and amt > 0: 
            spent += amt
            valid.append({"cat": cat, "val": val, "amt": amt})

    st.markdown(f"## 👤 Игрок №{player['id']}: {player['name']}")
    st.markdown(f"### Фишки: {player['balance_at_start'] - spent}")
    
    for i in range(st.session_state.bet_rows_count):
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1: 
            chosen_cat = st.selectbox("Тип", st.session_state.active_params, key=f"p{p_idx}_c{i}", on_change=save_game_state)
        with col2: 
            if chosen_cat in ["Год урожая", "Процент алкоголя"]:
                if chosen_cat == "Год урожая":
                    st.number_input("Ставка на год (точно)", min_value=1800, max_value=2026, step=1, key=f"p{p_idx}_v{i}", on_change=save_game_state)
                else:
                    st.number_input("Ставка на алкоголь (%)", min_value=0.0, max_value=25.0, step=0.1, key=f"p{p_idx}_v{i}", on_change=save_game_state)
                    st.caption("💡 Выигрыш в пределах ±0.5%")
            else:
                current_options = ["—"] + DATA[chosen_cat]
                correct_custom_val = st.session_state.current_wine.get(chosen_cat, "—")
                if correct_custom_val != "—" and correct_custom_val not in current_options:
                    current_options.append(correct_custom_val)
                st.selectbox("Ставка", current_options, key=f"p{p_idx}_v{i}", on_change=save_game_state)
                
        with col3: 
            st.number_input("Сумма", min_value=0, step=10, key=f"p{p_idx}_a{i}", on_change=save_game_state)
            
        if i == st.session_state.bet_rows_count - 1 and st.session_state.get(f"p{p_idx}_v{i}", "—") != "—" and st.session_state.get(f"p{p_idx}_a{i}", 0) > 0:
            st.session_state.bet_rows_count += 1
            save_game_state()
            st.rerun()
            
    col_nav1, col_nav2 = st.columns(2)
    if col_nav1.button("⬅️ Шаг назад", use_container_width=True):
        if st.session_state.current_player_idx > 0:
            st.session_state.current_player_idx -= 1
            st.session_state.bet_rows_count = 1
        else:
            st.session_state.page = "setup_wine"
        st.rerun()
            
    if col_nav2.button("Принять ход ➔", use_container_width=True, type="primary"):
        player['round_bets'] = valid
        player['balance'] = player['balance_at_start'] - spent
        if st.session_state.current_player_idx < len(st.session_state.players) - 1:
            st.session_state.current_player_idx += 1
            st.session_state.bet_rows_count = 1
        else: 
            st.session_state.page = "results"
        save_game_state()
        st.rerun()

# --- СТРАНИЦА 5: РЕЗУЛЬТАТЫ РАУНДА ---
def show_results():
    header()
    correct = st.session_state.current_wine
    st.markdown("## 📊 Итоги Раунда")
    
    display_answers = [f"{k}: {v}" for k, v in correct.items() if v != "—" and "raw" not in k]
    st.info("🎯 Ответ: " + " | ".join(display_answers))
    
    # Расчет результатов
    if f"calculated_r_{st.session_state.round_num}" not in st.session_state:
        for p in st.session_state.players:
            win = 0
            for b in p['round_bets']:
                # Логика проверки попадания
                if b['cat'] == "Процент алкоголя":
                    hit = abs(float(b['val']) - float(correct.get(b['cat'], 0))) <= 0.5
                elif b['cat'] == "Год урожая":
                    hit = int(b['val']) == int(correct.get(b['cat'], 0))  # Строгое совпадение
                else:
                    hit = str(b['val']).lower().strip() == str(correct.get(b['cat'])).lower().strip()
                
                win += b['amt'] * st.session_state.coeffs[b['cat']] if hit else 0
            p['balance'] = p['balance_at_start'] - sum(b['amt'] for b in p['round_bets']) + win
        st.session_state[f"calculated_r_{st.session_state.round_num}"] = True
        save_game_state()

    for p in sorted(st.session_state.players, key=lambda x: x['id']):
        win_sum = 0
        details = []
        for b in p['round_bets']:
            if b['cat'] == "Процент алкоголя":
                hit = abs(float(b['val']) - float(correct.get(b['cat'], 0))) <= 0.5
            elif b['cat'] == "Год урожая":
                hit = int(b['val']) == int(correct.get(b['cat'], 0))
            else:
                hit = str(b['val']).lower().strip() == str(correct.get(b['cat'])).lower().strip()
                
            res = b['amt'] * st.session_state.coeffs[b['cat']] if hit else 0
            win_sum += res
            details.append(f"<p style='color:{'#28a745' if hit else '#dc3545'}; margin:0;'>{'✅' if hit else '❌'} {b['cat']}: {b['val']} | {b['amt']} ➔ {res}</p>")
        
        with st.expander(f"👤 Игрок №{p['id']}: {p['name']} | Финальный баланс: {p['balance']}"):
            st.markdown("".join(details) or "Ставок нет", unsafe_allow_html=True)
            
    st.markdown("---")
    
    col_r1, col_r2 = st.columns(2)
    if col_r1.button("⬅️ Переиграть раунд (Назад)", use_container_width=True):
        if f"calculated_r_{st.session_state.round_num}" in st.session_state:
            del st.session_state[f"calculated_r_{st.session_state.round_num}"]
        for p in st.session_state.players:
            p['balance'] = p['balance_at_start']
        st.session_state.page = "betting"
        st.session_state.current_player_idx = len(st.session_state.players) - 1
        st.session_state.bet_rows_count = 1
        save_game_state()
        st.rerun()
        
    if col_r2.button("След. раунд 🍷", use_container_width=True, type="primary"):
        if f"calculated_r_{st.session_state.round_num}" in st.session_state:
            del st.session_state[f"calculated_r_{st.session_state.round_num}"]
        st.session_state.round_num += 1
        st.session_state.page = "setup_wine"
        st.session_state.current_wine = {}
        if st.session_state.shuffle_players:
            st.session_state.shuffle_order = random.sample(range(len(st.session_state.players)), len(st.session_state.players))
        else:
            st.session_state.shuffle_order = list(range(len(st.session_state.players)))
            
        for k in list(st.session_state.keys()):
            if any(x in k for x in ["_v", "_a", "_c"]): del st.session_state[k]
        save_game_state()
        st.rerun()
        
    st.write("")
    with st.popover("🚫 Завершить игру", use_container_width=True):
        st.warning("Вы уверены, что хотите закончить игру?")
        if st.button("Да, подтверждаю", use_container_width=True, type="primary"):
            st.session_state.page = "final"
            save_game_state()
            st.rerun()

# --- СТРАНИЦА 6: ФИНАЛ ---
def show_final():
    header()
    st.markdown("<h1 style='text-align: center;'>🏆 Финал</h1>", unsafe_allow_html=True)
    
    for i, p in enumerate(sorted(st.session_state.players, key=lambda x: x['balance'], reverse=True)):
        st.write(f"**{i+1}. Игрок №{p['id']}: {p['name']}** — {p['balance']} фишек")
        
    st.markdown("---")
    
    col_f1, col_f2 = st.columns(2)
    if col_f1.button("⬅️ К результатам раунда", use_container_width=True):
        st.session_state.page = "results"
        st.rerun()
        
    if col_f2.button("Заново 🔄", use_container_width=True, type="primary"):
        clear_game_backup()
        st.session_state.clear()
        st.rerun()

# --- РОУТИНГ ЭКРАНОВ ---
if st.session_state.page == "setup_params": show_setup_params()
elif st.session_state.page == "registration": show_registration()
elif st.session_state.page == "setup_wine": show_setup_wine()
elif st.session_state.page == "betting": show_betting()
elif st.session_state.page == "results": show_results()
elif st.session_state.page == "final": show_final()
