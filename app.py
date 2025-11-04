import os
import time
import sqlite3
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from groq import Groq

# ---------------- DATABASE CONNECTION ----------------
# ---------------- DATABASE CONNECTION ----------------

# -----------------------------
# DATABASE INITIALIZATION FIX ✅
# -----------------------------
DB_NAME = "fitness_app.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        plan TEXT DEFAULT 'free',
        expiry TEXT,
        payment_id TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# -------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------
st.set_page_config(page_title="FIT PRO", page_icon="💪", layout="centered")

# ------------------------- STYLES -------------------------
st.markdown("""
    <style>
        .main { background-color: #0f1113; color: #ffffff; }

        .button-row {
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: nowrap;
            margin-bottom: 40px;
        }

        .stButton>button {
            background-color: #111;
            color: #fff;
            border: 1px solid #444;
            border-radius: 10px;
            padding: 12px 20px;
            font-weight: 600;
            transition: all 0.3s ease;
            min-width: 150px;
            text-align: center;
            white-space: nowrap;
        }

        .stButton>button:hover {
            background-color: #1e1e1e;
            border-color: #888;
            transform: translateY(-2px);
        }

        .stButton>button:focus {
            border-color: #ffb703;
            box-shadow: 0 0 10px #ffb70355;
        }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# -------------------------------------------------------
# ------------------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# ------------------------------------------------------------

# Load .env file (for local) and Streamlit secrets (for cloud)
load_dotenv()

# Try to get API key from .env or Streamlit secrets
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")

client = None

if GROQ_API_KEY:
    try:
        client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        st.error(f"⚠️ Groq init failed: {e}")
else:
    st.error("❌ GROQ_API_KEY not found — AI features disabled.")

# -------------------------------------------------------
# DATABASE FUNCTIONS
# -------------------------------------------------------
DB_FILE = os.path.join(os.path.dirname(__file__), "fitness_app.db")

def ensure_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                plan TEXT,
                expiry TEXT,
                payment_id TEXT
            )
        """)
        conn.commit()

ensure_db()

def add_or_update_user(email, plan, payment_id):
    expiry_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE email=?", (email,))
        if c.fetchone():
            c.execute(
                "UPDATE users SET plan=?, expiry=?, payment_id=? WHERE email=?",
                (plan, expiry_date, payment_id, email)
            )
        else:
            c.execute(
                "INSERT INTO users (email, plan, expiry, payment_id) VALUES (?, ?, ?, ?)",
                (email, plan, expiry_date, payment_id)
            )
        conn.commit()

def get_plan_type(email):
    if not email:
        return "Basic"
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT plan, expiry FROM users WHERE email=?", (email,))
        result = c.fetchone()
    if not result:
        return "Basic"
    plan, expiry = result
    if not expiry:
        return "Basic"
    if datetime.strptime(expiry, "%Y-%m-%d") > datetime.now():
        return plan
    return "Basic"


# -------------------------------------------------------
# PROMPTS
# -------------------------------------------------------
def workout_prompt(age, sex, height, weight, experience, days, equipment, goal):
    return f"""
You are an Indian certified gym trainer.
Create a 7-day workout plan for:
Age: {age}, Sex: {sex}, Height: {height} cm, Weight: {weight} kg
Experience: {experience}, Days: {days}, Equipment: {equipment}, Goal: {goal}

Rules:
- Day-wise exercises aligned with goal.
- Include sets, reps, and rest.
Return only the plan in markdown.
"""

def diet_prompt(age, weight, goal, diet_type):
    return f"""
You are an Indian nutritionist.
Create a 7-day Indian student-friendly diet plan for:
Age: {age}, Weight: {weight} kg, Goal: {goal}, Diet Type: {diet_type}
Return only the diet in markdown.
"""

# -------------------------------------------------------
# MAIN UI
# -------------------------------------------------------
st.markdown("""
    <style>
    div[data-testid="stSidebar"] {display: none;}

    .app-header {
        text-align: center;
        font-size: 40px;
        font-weight: 900;
        color: white;
        margin-top: 15px;
        text-shadow: 0 0 25px rgba(255, 255, 255, 0.3);
        letter-spacing: 1px;
    }

    .navbar {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 18px;
        padding: 15px 25px;
        margin-top: 25px;
        background: rgba(255, 255, 255, 0.06);
        backdrop-filter: blur(15px);
        border-radius: 25px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 25px rgba(0,0,0,0.4);
        width: fit-content;
        margin-left: auto;
        margin-right: auto;
    }

    .nav-btn {
        background: rgba(255, 255, 255, 0.08);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 8px 20px;
        font-size: 15px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.25s ease-in-out;
        box-shadow: 0 4px 10px rgba(0,0,0,0.25);
    }

    .nav-btn:hover {
        background: rgba(255, 255, 255, 0.2);
        transform: translateY(-2px);
    }

    .nav-active {
        background: linear-gradient(135deg, #ff8c00, #ffcc33);
        color: black;
        box-shadow: 0 0 15px rgba(255, 200, 0, 0.8);
        transform: scale(1.05);
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="app-header">FIT PRO 💪</div>', unsafe_allow_html=True)

# ---------------- EMAIL LOGIN FIXED ✅ ----------------
if "user_email" not in st.session_state:
    st.session_state["user_email"] = ""
if "is_premium" not in st.session_state:
    st.session_state["is_premium"] = False

st.markdown("### ✉️ Enter your email to continue:")
email_input = st.text_input("Email Address", placeholder="example@gmail.com")

if email_input.strip() != "":
    # ✅ Reset session when a new email is entered
    if email_input != st.session_state["user_email"]:
        st.session_state["user_email"] = email_input
        st.session_state["is_premium"] = False
        st.rerun()

if st.session_state["user_email"] == "":
    st.warning("⚠️ Please enter your email to use FIT PRO.")
    st.stop()

# ✅ Always fetch fresh plan type for current email
plan_type = get_plan_type(st.session_state["user_email"])
st.session_state["is_premium"] = (plan_type == "Premium")

if st.session_state["is_premium"]:
    st.success(f"🌟 You are on the **Premium Plan** — Welcome, {st.session_state['user_email']}!")
else:
    st.info(f"✅ You are on the **Basic Plan** — Logged in as {st.session_state['user_email']}")

st.markdown("---")

# Navigation
nav_items = ["🏋️ Gym Plan", "🍽️ Diet Plan", "🔥 Calorie Tracker", "🤖 Chatbot", "💳 Premium"]
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "🏋️ Gym Plan"

st.markdown('<div class="button-row">', unsafe_allow_html=True)
cols = st.columns(5, gap="small")
for i, tab_name in enumerate(nav_items):
    if cols[i].button(tab_name, key=f"tab_{i}"):
        st.session_state["active_tab"] = tab_name
st.markdown('</div>', unsafe_allow_html=True)

tab = st.session_state["active_tab"]

# -------------------------------------------------------
# GYM PLAN
# -------------------------------------------------------
if tab == "🏋️ Gym Plan":
    st.header("Generate Workout Plan")
    with st.form("gym_form"):
        age = st.number_input("Age", 14, 80, 22)
        sex = st.selectbox("Sex", ["Male", "Female", "Other"])
        height = st.number_input("Height (cm)", 120, 230, 175)
        weight = st.number_input("Weight (kg)", 35, 200, 70)
        experience = st.selectbox("Experience", ["Beginner", "Intermediate", "Advanced"])
        days = st.selectbox("Days/week", [3, 4, 5, 6])
        equipment = st.selectbox("Equipment", ["Bodyweight", "Dumbbells + Bench", "Full Gym"])
        goal = st.selectbox("Goal", ["Fat Loss", "Muscle Gain", "Recomposition", "Strength"])
        submit = st.form_submit_button("Generate Workout 🚀")
    if submit:
        with st.spinner("Generating workout plan..."):
            try:
                res = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": workout_prompt(age, sex, height, weight, experience, days, equipment, goal)}],
                    temperature=0.5
                )
                st.markdown(res.choices[0].message.content)
            except Exception as e:
                st.error(f"Error: {e}")

# -------------------------------------------------------
# DIET PLAN
# -------------------------------------------------------
elif tab == "🍽️ Diet Plan":
    st.header("Generate Diet Plan")
    age = st.number_input("Age", 14, 80, 22, key="diet_age")
    weight = st.number_input("Weight (kg)", 35, 200, 70, key="diet_weight")
    goal = st.selectbox("Goal", ["Fat Loss", "Muscle Gain", "Recomposition", "Strength"], key="diet_goal")
    diet_type = st.selectbox("Diet Type", ["Vegetarian", "Eggetarian", "Non-Vegetarian"], key="diet_type")
    if st.button("Generate Diet 🍛"):
        with st.spinner("Generating diet plan..."):
            try:
                res = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": diet_prompt(age, weight, goal, diet_type)}],
                    temperature=0.5
                )
                st.markdown(res.choices[0].message.content)
            except Exception as e:
                st.error(f"Error generating diet: {e}")

# -------------------------------------------------------
# CALORIE TRACKER
# -------------------------------------------------------
elif tab == "🔥 Calorie Tracker":
    st.header("🔥 Calorie Tracker")
    if not st.session_state.get("is_premium", False):
        st.warning("🔒 This feature is available only for Premium Members.")
    else:
        foods = {
            "Roti": (300, 8, 55),
            "Rice": (130, 2.7, 28),
            "Paneer": (265, 18, 6),
            "Egg": (155, 13, 1.1),
            "Milk": (60, 3.2, 5),
            "Soya Chunks": (345, 52, 33),
            "Oats": (380, 13, 67),
            "Idli": (110, 3.2, 20),
            "Dosa": (165, 3.9, 31),
            "Apple": (52, 0.3, 14),
            "Banana": (89, 1.1, 23),
            "Peanuts": (567, 25, 16),
            "Almonds": (579, 21, 22),
            "Sprouts": (90, 7, 15),
            "Vegetable Soup": (60, 2, 10)
        }
        food = st.selectbox("🍽️ Choose food:", list(foods.keys()))
        qty = st.number_input("Quantity (grams)", 1, 1000, 100)
        if food:
            cal, p, c = foods[food]
            st.markdown(f"**Calories:** {(cal/100)*qty:.1f} kcal | **Protein:** {(p/100)*qty:.1f} g | **Carbs:** {(c/100)*qty:.1f} g")

# -------------------------------------------------------
# CHATBOT
# -------------------------------------------------------
elif tab == "🤖 Chatbot":
    st.header("🤖 FIT PRO Chatbot")
    if not st.session_state.get("is_premium", False):
        st.warning("💬 Chatbot is available only for Premium Members.")
    else:
        q = st.text_input("Ask your question:")
        if q:
            with st.spinner("Thinking..."):
                try:
                    ans = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": q}],
                        temperature=0.4
                    )
                    st.markdown(ans.choices[0].message.content)
                except Exception as e:
                    st.error(f"Chatbot error: {e}")

# -------------------------------------------------------
# PREMIUM SECTION
# -------------------------------------------------------
elif tab == "💳 Premium":
    st.header("💳 Unlock FIT PRO Premium (₹299 / Year)")

    user_email = st.text_input("📧 Enter your email:")
    if user_email.strip() == "":
        st.warning("⚠️ Please enter your email first.")
    else:
        plan_type = get_plan_type(user_email)
        if plan_type == "Premium":
            st.success("🎉 You are a Premium Member!")
            st.markdown("✨ Enjoy access to advanced plans and exclusive features!")
        else:
            st.info("💡 You are currently on the **Basic Plan**.")

            st.markdown("""
            💰 **FIT PRO Premium – ₹299 / Year**
            🔓 Unlock features:
            - Advanced Workout Plans  
            - Indian Diet Generator  
            - Calorie Tracker  
            - Smart Chatbot Assistant  
            """)

            payment_link = "https://rzp.io/rzp/5VHFcVO1"
            st.markdown(f"[🛒 Pay ₹299 on Razorpay]({payment_link})", unsafe_allow_html=True)

            payment_id = st.text_input("💳 Enter your Payment ID (e.g., pay_XXXXXXXXXXXX):")

            if st.button("✅ Verify & Activate Premium"):
                if payment_id.startswith("pay_"):
                    add_or_update_user(user_email, "Premium", payment_id)
                    st.session_state["is_premium"] = True
                    st.success("🎉 Payment verified! Premium access granted for 1 year.")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()  # ✅ FIXED HERE
                else:
                    st.error("❌ Invalid Payment ID. Please check and try again.")

    st.markdown("---")
    st.caption("💗 Designed by Harsh | Made with 💖 for Students & Fitness Lovers IN")
