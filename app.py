import streamlit as st
import google.generativeai as genai
import random

# --- 1. КОНФИГУРАЦИЯ ДАННЫХ ---
DATA = {
    "Сладость": [
        "сухое", "полусухое", "полусладкое", "сладкое"
    ],
    "Страна": [
        "Россия", "ЮАР", "Австралия", "Аргентина", "США", 
        "Новая Зеландия", "Чили", "Франция", "Италия", "Испания", 
        "Австрия", "Германия", "Португалия", "Грузия", "Армения"
    ],
    "Сорт винограда": [
        "Шардоне", "Рислинг", "Совиньон Блан", "Пино Гриджио", 
        "Гевюрцтраминер", "Кортезе", "Гарганега", "Альбариньо", 
        "Вердехо", "Грюнер Вельтлинер", "Каберне Совиньон", "Мерло", 
        "Пино Нуар", "Сира/Шираз", "Темпранильо", "Санджовезе", 
        "Мальбек", "Красностоп", "Саперави"
    ],
    "Выдержка": [
        "выдержано в дубе", "не выдержано в дубе", "выдержано на осадке"
    ]
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
    if not model: 
        return "ИИ временно ушел в погреб. Проверьте API-ключ."
    
    seed = random.randint(1, 100000)
    
    if "страну" in target_type.lower():
        logic = (
            "Твоя цель — дать легкий, изящный намек.\n"
            "ЗАПРЕЩЕНО: называть соседей, части света, моря, горы, столицы, флаги или валюту.\n"
            "ИЗБЕГАЙ: очевидных фактов (типа 'родина пиццы' или 'страна кенгуру').\n"
            "ФОКУС: Этимология, древние законы, уникальные находки или странные традиции."
        )
    else:
        logic = (
            "Твоя цель — загадка для профи.\n"
            "ЗАПРЕЩЕНО: описывать вкус, ароматы, цвет или называть регионы-лидеры.\n"
            "ФОКУС: Генеалогия лозы, форма листа, исторические курьезы 500 лет назад."
        )

    prompt = (
        f"Мы играем в винное казино. Дай ОДНУ подсказку про {target_type} '{target_value}'.\n"
        f"ID запроса: {seed}\n\n"
        f"{logic}\n\n"
        "ПРАВИЛА ИСПОЛНЕНИЯ:\n"
        f"1. КАТЕГОРИЧЕСКИ НЕ НАЗЫВАЙ '{target_value}'.\n"
        "2. Пиши изысканно, 2-3 законченных предложения.\n"
        "3. Не используй вводные слова. Сразу к сути.\n"
        "4. ОБЯЗАТЕЛЬНО закончи мысль точкой."
    )
    
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
                return "ИИ задумался. Нажмите кнопку еще раз."
        
        return res
    except Exception as e:
        return f"Техническая заминка: {str(e)}"

# --- 3. УПРАВЛЕНИЕ СОСТОЯНИЕМ (РАЗБИТО НА КОРОТКИЕ СТРОКИ) ---
if "players" not in st.session_state:
    st.session_state["players"] = []
if "page" not in st.session_state:
    st.session_state["page"] = "registration"
if "round_num" not in st.session_state:
    st.session_state["round_num"] = 1
if "current_wine" not in st.session_state:
    st.session_state["current_wine"] = {}
if "bet_rows_count" not in st.session_state:
    st.session_state["bet_rows_count"] = 1
if "hints" not in st.session_state:
    st.session_state["hints"] = {"country": "", "grape": ""}
if "current_player_idx" not in st.session_state:
    st.session_state["current_player_idx"] = 0
if "last_country" not in st.session_state:
    st.session_state["last_country"] = "—"
if "last_grape" not in st.
