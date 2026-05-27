import streamlit as st
import google.generativeai as genai
import random
import json
import os

BACKUP_FILE = "wine_casino_backup.json"

# --- ФУНКЦИИ ЗАЩИТЫ ОТ СБРОСА СЕССИИ ---
def save_game_state():
    """Сохраняет критически важные данные игры на диск"""
    state_to_save = {}
    for k in ["players", "page", "round_num", "current_wine", "bet_rows_count", "hints", "current_player_idx", "last_country", "last_grape"]:
        if k in st.session_state:
            state_to_save[k] = st.session_state[k]
    
    # Также сохраняем динамические ключи ставок (выборы в селектбоксах и инпутах)
    dynamic_keys = {k: st.session_state[k] for k in st.session_state.keys() if any(x in k for x in ["_v", "_a", "_c"])}
    state_to_save["dynamic_keys"] = dynamic_keys

    with open(BACKUP_FILE, "w", encoding="utf-8") as f:
        json.dump(state_to_save, f, ensure_ascii=False, indent=4)

def load_game_state():
    """Восстанавливает данные игры при обновлении страницы"""
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
    """Удаляет файл бэкапа при полном перезапуске игры"""
    if os.path.exists(BACKUP_FILE):
        try: os.remove(BACKUP_FILE)
        except: pass

# Инициализируем восстановление до создания дефолтных ключей
load_game_state()

# --- 1. ДАННЫЕ И КОНФИГУРАЦИЯ ---
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
            return None, "Ключ не найден в Secrets"
        
        # Прямая конфигурация без лишних проверок
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        
        # Самое прямое и базовое имя модели в библиотеке
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        return model, "ОК: gemini-1.5-flash"
    except Exception as e: 
        return None, f"Ошибка при старте: {str(e)}"

if "ai_model" not in st.session_state:
    m, s = initialize_ai()
    st.session_state.ai_model, st.session_state.ai_status = m, s

def get_ai_hint(t_type, t_val):
    model = st.session_state.ai_model
    if not model: return "ИИ в погребе."
    
    seed = random.randint(1, 999999)
    
    if "страну" in t_type.lower():
        prompt = f"""
        Ты — сомелье-историк игры 'Винное Казино'. Твоя задача — дать ОДНУ сложную подсказку про страну: '{t_val}'.
        Уникальный маркер: {seed}.

        ПРАВИЛА КОНТЕНТА:
        1. Полный запрет на географию соседей и моря (никаких 'Кавказ', 'Черное море', 'вблизи Европы').
        2. ЗАПРЕЩЕНЫ СЛОВА-МАРКЕРЫ: Русь, православные, славяне, царь, СССР, березы, Кремль, водка, кенгуру, пицца, Эйфелева, Колизей, столицы, валюта.
        3. ФОКУС: Исторические курьезы, наука, космос, необычные законы.

        ФОРМАТ ОТВЕТА (СТРОГО):
        Напиши ровно 2 факта в формате нумерованного списка (1. и 2.). Каждый факт — ровно одно полное, законченное предложение. Пиши слова полностью, без сокращений. Не называй слово '{t_val}'.
        """
    else:
        prompt = f"""
        Ты — сомелье-ампелограф игры 'Винное Казино'. Твоя задача — дать ОДНУ сложную подсказку про сорт винограда: '{t_val}'.
        Уникальный маркер: {seed}.

        ПРАВИЛА КОНТЕНТА:
        1. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО описывать вкусовые и ароматические качества (ягоды, кожа, цитрус, бензол, танины).
        2. Запрещено называть ключевые регионы (Бордо, Бургундия, Каор, Мендоса, Мальборо).
        3. ФОКУС: Происхождение названия (этимология), ботанические особенности лозы или листа, исторические легенды. Избегай слов 'мутация' и 'генетика'.

        ФОРМАТ ОТВЕТА (СТРОГО):
        Напиши ровно 2 факта в формате нумерованного списка (1. и 2.). Каждый факт — ровно одно полное, законченное предложение. Пиши слова полностью, без сокращений. Не называй сорт '{t_val}'.
        """

    try:
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}
        ]
        
        # Обычный текстовый режим, но с жесткой структурой списка
        resp = model.generate_content(
            prompt, 
            generation_config=genai.types.GenerationConfig(
                temperature=0.6, 
                max_output_tokens=800,
                top_p=0.9
            ),
            safety_settings=safety_settings
        )
        
        res = resp.text.strip().replace('"', '')
        if not res:
            return "Не удалось получить ответ от ИИ. Попробуйте обновить."
        return res
        
    except Exception as e: 
        # Если произошла ошибка, мы выведем её текст прямо на экран, чтобы понять, в чем дело
        return f"Ошибка связи с ИИ: {str(e)}. Пожалуйста, нажмите кнопку обновления еще раз."

# --- 3. ИНИЦИАЛИЗАЦИЯ БАЗОВЫХ КЛЮЧЕЙ СЕССИИ ---
keys = ["players", "page", "round_num", "current_wine", "bet_rows_count", "hints", "current_player_idx", "last_country", "last_grape"]
defs = [[], "registration", 1, {}, 1, {"country": "", "grape": ""}, 0, "—", "—"]
for k, d in zip(keys, defs):
    if k not in st.session_state: st.session_state[k] = d

def header(show_logo=False):
    if show_logo:
        try: st.image("logo.png", width=250)
        except: st.write("### WINE & WHISKEY")
    st.markdown("---")

# --- 4. СТРАНИЦЫ ИГРЫ ---
def show_registration():
    header(True)
    st.markdown("<h2 style='text-align: center;'>📝 Регистрация</h2>", unsafe_allow_html=True)
    with st.form("reg_form", clear_on_submit=True):
        name = st.text_input("Имя игрока:")
        if st.form_submit_button("Добавить", use_container_width=True) and name.strip():
            st.session_state.players.append({"name": name.strip(), "balance": 150, "round_bets": [], "balance_at_start": 150})
            save_game_state()
            st.rerun()
    if st.session_state.players:
        for p in st.session_state.players: st.write(f"✅ {p['name']}")
        if st.button("Начать игру ➔", use_container_width=True, type="primary"):
            st.session_state.page = "setup"
            save_game_state()
            st.rerun()

def show_setup():
    header()
    st.markdown(f"### 🍷 Раунд №{st.session_state.round_num}")
    c1, c2 = st.columns([1, 1.2])
    with c1:
        st.markdown("#### Параметры")
        for cat, opts in DATA.items():
            old_val = st.session_state.current_wine.get(cat, "—")
            new_val = st.selectbox(f"{cat}:", ["—"] + opts, key=f"s_{cat}")
            if new_val != old_val:
                st.session_state.current_wine[cat] = new_val
                save_game_state()
    
    c_count = st.session_state.current_wine.get("Country" if "Country" in st.session_state.current_wine else "Страна", "—")
    c_grape = st.session_state.current_wine.get("Grape" if "Grape" in st.session_state.current_wine else "Сорт винограда", "—")
    
    if c_count != "—" and c_count != st.session_state.last_country:
        st.session_state.hints["country"] = get_ai_hint("страну", c_count)
        st.session_state.last_country = c_count
        save_game_state()
    if c_grape != "—" and c_grape != st.session_state.last_grape:
        st.session_state.hints["grape"] = get_ai_hint("сорт винограда", c_grape)
        st.session_state.last_grape = c_grape
        save_game_state()

    with c2:
        st.markdown("#### Подсказки ИИ")
        if c_count != "—":
            st.info(st.session_state.hints["country"] or "Ждем ИИ...")
            if st.button("🔄 Обновить Страну"):
                st.session_state.hints["country"] = get_ai_hint("страну", c_count)
                save_game_state(); st.rerun()
        if c_grape != "—":
            st.success(st.session_state.hints["grape"] or "Ждем ИИ...")
            if st.button("🔄 Обновить Сорт"):
                st.session_state.hints["grape"] = get_ai_hint("сорт винограда", c_grape)
                save_game_state(); st.rerun()
                
    st.markdown("---")
    if st.button("К ставкам ➔", use_container_width=True, type="primary"):
        for p in st.session_state.players: p['balance_at_start'] = p['balance']
        st.session_state.page = "betting"
        st.session_state.current_player_idx = 0
        st.session_state.bet_rows_count = 1
        save_game_state()
        st.rerun()

def show_betting():
    header()
    p_idx = st.session_state.current_player_idx
    player = st.session_state.players[p_idx]
    spent, valid = 0, []
    
    for i in range(st.session_state.bet_rows_count):
        cat = st.session_state.get(f"p{p_idx}_c{i}", "Сладость")
        val = st.session_state.get(f"p{p_idx}_v{i}", "—")
        amt = st.session_state.get(f"p{p_idx}_a{i}", 0)
        if val != "—" and amt > 0: 
            spent += amt
            valid.append({"cat": cat, "val": val, "amt": amt})

    st.markdown(f"## 👤 {player['name']}")
    st.markdown(f"### Фишки: {player['balance'] - spent}")
    
    for i in range(st.session_state.bet_rows_count):
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1: 
            st.selectbox("Тип", list(COEFFS.keys()), key=f"p{p_idx}_c{i}", on_change=save_game_state)
        with col2: 
            st.selectbox("Ставка", ["—"] + DATA[st.session_state[f"p{p_idx}_c{i}"]], key=f"p{p_idx}_v{i}", on_change=save_game_state)
        with col3: 
            st.number_input("Сумма", min_value=0, step=10, key=f"p{p_idx}_a{i}", on_change=save_game_state)
            
        if i == st.session_state.bet_rows_count - 1 and st.session_state.get(f"p{p_idx}_v{i}", "—") != "—" and st.session_state.get(f"p{p_idx}_a{i}", 0) > 0:
            st.session_state.bet_rows_count += 1
            save_game_state()
            st.rerun()
            
    if st.button("Принять", use_container_width=True, type="primary"):
        player['round_bets'], player['balance'] = valid, player['balance'] - spent
        if st.session_state.current_player_idx < len(st.session_state.players) - 1:
            st.session_state.current_player_idx += 1
            st.session_state.bet_rows_count = 1
        else: 
            st.session_state.page = "results"
        save_game_state()
        st.rerun()

def show_results():
    header()
    correct = st.session_state.current_wine
    st.markdown("## 📊 Итоги Раунда")
    st.info("🎯 Ответ: " + " | ".join([f"{k}: {v}" for k, v in correct.items() if v != "—"]))
    
    # Расчет результатов происходит один раз при переходе на страницу результатов
    if f"calculated_r_{st.session_state.round_num}" not in st.session_state:
        for p in st.session_state.players:
            win = 0
            for b in p['round_bets']:
                hit = str(b['val']).lower() == str(correct.get(b['cat'])).lower()
                win += b['amt'] * COEFFS[b['cat']] if hit else 0
            p['balance'] += win
        st.session_state[f"calculated_r_{st.session_state.round_num}"] = True
        save_game_state()

    for p in st.session_state.players:
        win_sum = 0
        details = []
        for b in p['round_bets']:
            hit = str(b['val']).lower() == str(correct.get(b['cat'])).lower()
            res = b['amt'] * COEFFS[b['cat']] if hit else 0
            win_sum += res
            details.append(f"<p style='color:{'#28a745' if hit else '#dc3545'}; margin:0;'>{'✅' if hit else '❌'} {b['cat']}: {b['val']} | {b['amt']} ➔ {res}</p>")
        
        with st.expander(f"👤 {p['name']} | Выигрыш: +{win_sum}"):
            st.markdown("".join(details) or "Ставок нет", unsafe_allow_html=True)
            st.write(f"Баланс: {p['balance']}")
            
    c1, c2 = st.columns(2)
    if c1.button("След. раунд 🍷", use_container_width=True):
        st.session_state.round_num += 1
        st.session_state.page = "setup"
        st.session_state.hints = {"country": "", "grape": ""}
        st.session_state.last_country, st.session_state.last_grape = "—", "—"
        for k in list(st.session_state.keys()):
            if any(x in k for x in ["_v", "_a", "_c"]): del st.session_state[k]
        save_game_state()
        st.rerun()
    if c2.button("Финал 🏆", use_container_width=True, type="primary"): 
        st.session_state.page = "final"
        save_game_state()
        st.rerun()

def show_final():
    header()
    st.markdown("<h1>🏆 Финал</h1>", unsafe_allow_html=True)
    for i, p in enumerate(sorted(st.session_state.players, key=lambda x: x['balance'], reverse=True)):
        st.write(f"**{i+1}. {p['name']}** — {p['balance']} фишек")
        
    if st.button("Заново 🔄", use_container_width=True, type="primary"):
        clear_game_backup()
        st.session_state.clear()
        st.rerun()

# --- 5. РОУТИНГ ---
if st.session_state.page == "registration": show_registration()
elif st.session_state.page == "setup": show_setup()
elif st.session_state.page == "betting": show_betting()
elif st.session_state.page == "results": show_results()
elif st.session_state.page == "final": show_final()
