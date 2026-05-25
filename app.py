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
    Мы играем в винное казино. Дай
