import os
import time
import sqlite3
import json
from datetime import datetime, timedelta
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

# -------------------------------------------------------
# STREAMLIT CONFIG
# -------------------------------------------------------
st.set_page_config(page_title="FIT PRO 💪", page_icon="💪", layout="centered")

# -------------------------------------------------------
# ✅ PWA INSTALL FEATURE
# -------------------------------------------------------
st.markdown("""
<link rel="manifest" href="manifest.json">
<meta name="theme-color" content="#FFD700">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="FIT PRO 💪">
<link rel="apple-touch-icon" href="static/icons/icon-192.png">
<link rel="icon" href="static/icons/icon-192.png" type="image/png">

<script>
// Register service worker
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('service_worker.js')
  .then(() => console.log('✅ Service Worker Registered'))
  .catch(err => console.log('❌ Service Worker Failed:', err));
}

// Smart install prompt
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;

  if (!localStorage.getItem('fitpro_install_prompted')) {
    const btn = document.createElement('button');
    btn.textContent = "📲 Install FIT PRO";
    btn.style.position = 'fixed';
    btn.style.bottom = '30px';
    btn.style.right = '20px';
    btn.style.background = 'linear-gradient(135deg, #FFD700, #b8860b)';
    btn.style.color = 'black';
    btn.style.padding = '12px 20px';
    btn.style.border = 'none';
    btn.style.borderRadius = '10px';
    btn.style.fontWeight = '700';
    btn.style.cursor = 'pointer';
    btn.style.boxShadow = '0 4px 15px rgba(0,0,0,0.3)';
    btn.style.zIndex = '9999';
    document.body.appendChild(btn);

    btn.addEventListener('click', async () => {
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      if (outcome === 'accepted') {
        console.log('✅ Installed FIT PRO');
        localStorage.setItem('fitpro_install_prompted', 'true');
        btn.remove();
      }
      deferredPrompt = null;
    });
  }
});

window.addEventListener('appinstalled', () => {
  console.log('🎉 FIT PRO installed!');
  localStorage.setItem('fitpro_install_prompted', 'true');
});
</script>
""", unsafe_allow_html=True)


# -------------------------------------------------------
# DATABASE SETUP
# -------------------------------------------------------
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
# LOAD ENVIRONMENT VARIABLES
# -------------------------------------------------------
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
client = None
if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)
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
            c.execute("UPDATE users SET plan=?, expiry=?, payment_id=? WHERE email=?",
                      (plan, expiry_date, payment_id, email))
        else:
            c.execute("INSERT INTO users (email, plan, expiry, payment_id) VALUES (?, ?, ?, ?)",
                      (email, plan, expiry_date, payment_id))
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
# HEADER
# -------------------------------------------------------
st.markdown("""
<style>
.app-header {
    text-align: center;
    font-size: 65px;
    font-weight: 900;
    margin-top: 40px;
    letter-spacing: 2px;
    text-transform: uppercase;
    background: linear-gradient(90deg, #00c6ff, #0072ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 0 20px rgba(0, 140, 255, 0.6), 0 0 40px rgba(0, 140, 255, 0.3);
}
</style>
""", unsafe_allow_html=True)
st.markdown('<div class="app-header">FIT PRO 💪</div>', unsafe_allow_html=True)


# -------------------------------------------------------
# EMAIL LOGIN
# -------------------------------------------------------
if "user_email" not in st.session_state:
    st.session_state["user_email"] = ""
if "is_premium" not in st.session_state:
    st.session_state["is_premium"] = False

st.markdown("✉️ Enter your email to continue:")
email_input = st.text_input("Email Address", placeholder="example@gmail.com")

import re
def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None

if email_input.strip() != "":
    if not is_valid_email(email_input):
        st.error("❌ Invalid email format.")
        st.stop()
    else:
        if email_input != st.session_state["user_email"]:
            st.session_state["user_email"] = email_input
            st.session_state["is_premium"] = False
            st.rerun()

if st.session_state["user_email"] == "":
    st.warning("⚠️ Please enter your email to use FIT PRO.")
    st.stop()

plan_type = get_plan_type(st.session_state["user_email"])
st.session_state["is_premium"] = (plan_type == "Premium")

if st.session_state["is_premium"]:
    st.success(f"🌟 You are on the Premium Plan — Welcome, {st.session_state['user_email']}!")
else:
    st.info(f"✅ Basic Plan — Logged in as {st.session_state['user_email']}")

st.markdown("---")


# -------------------------------------------------------
# NAVIGATION
# -------------------------------------------------------
# =========================
# NAVIGATION + UI TABS (GLOWING VERSION)
# =========================
# =========================
# NAVIGATION (ELECTRIC BLUE FIXED)
# =========================

tabs = ["🏋️ Gym Plan", "🍽️ Diet Plan", "🔥 Calorie Tracker", "🤖 Chatbot", "💳 Premium"]

# Initialize tab safely
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = tabs[0]

# CSS Styling
st.markdown("""
<style>
.button-row {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin: 25px auto 30px;
  flex-wrap: nowrap;
  overflow-x: auto;
}
.stButton>button {
  background-color: #12151a;
  color: #f0f6ff;
  border: 1px solid #26313f;
  border-radius: 14px;
  width: 170px;
  height: 52px;
  font-weight: 700;
  font-size: 15px;
  transition: all 0.25s ease-in-out;
  box-shadow: 0 6px 18px rgba(0,0,0,.25);
}
.stButton>button:hover {
  border-color: #00c6ff;
  box-shadow: 0 0 14px #00c6ff80;
  transform: translateY(-1px);
}
.active-btn {
  border-color: #00c6ff !important;
  color: #ffffff !important;
  background: linear-gradient(145deg, #00c6ff33, #004aad55);
  box-shadow: 0 0 25px #00c6ff88, inset 0 0 12px #00c6ff44 !important;
  transform: scale(1.05);
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0% { box-shadow: 0 0 10px #00c6ff80, inset 0 0 8px #00c6ff55; }
  50% { box-shadow: 0 0 20px #00c6ffbb, inset 0 0 14px #00c6ff88; }
  100% { box-shadow: 0 0 10px #00c6ff80, inset 0 0 8px #00c6ff55; }
}
</style>
""", unsafe_allow_html=True)

# Render the tabs
st.markdown('<div class="button-row">', unsafe_allow_html=True)
cols = st.columns(len(tabs), gap="small")

for i, label in enumerate(tabs):
    # Give each button a unique key
    btn_clicked = cols[i].button(label, key=f"tab_{i}")
    # If this tab is active, inject a JS tweak to make it look glowing
    if label == st.session_state["active_tab"]:
        st.markdown(
            f"""
            <script>
            var btn = window.parent.document.querySelectorAll('button[k="tab_{i}"]')[0];
            if (btn) {{
                btn.classList.add('active-btn');
            }}
            </script>
            """,
            unsafe_allow_html=True
        )
    if btn_clicked:
        st.session_state["active_tab"] = label

st.markdown('</div>', unsafe_allow_html=True)

# Store active tab
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


# ------------------------------------------------------
# 🥗 DIET PLAN (PREMIUM FEATURE)
# ------------------------------------------------------
elif tab == "🍽️ Diet Plan":
    st.header("🥗 Personalized Diet Plan")

    if st.session_state.get("is_premium", False):
        age = st.number_input("Age", 14, 80, 22, key="diet_age")
        weight = st.number_input("Weight (kg)", 35, 200, 70, key="diet_weight")
        goal = st.selectbox("Goal", ["Fat Loss", "Muscle Gain", "Recomposition", "Strength"], key="diet_goal")
        diet_type = st.selectbox("Diet Type", ["Vegetarian", "Eggetarian", "Non-Vegetarian"], key="diet_type")

        if st.button("Generate Premium Diet 🍱"):
            with st.spinner("Crafting your personalized premium diet plan..."):
                try:
                    prompt = f"Create a detailed 7-day Indian diet plan for a {diet_type} who wants {goal}. Age: {age}, Weight: {weight}kg."
                    res = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.5,
                    )
                    st.success("🎯 Premium Diet Plan Generated!")
                    st.markdown(res.choices[0].message.content)
                except Exception as e:
                    st.error(f"Error generating diet plan: {e}")
    else:
        st.warning("🚫 Premium Members Only.")


# -------------------------------------------------------
# 🔥 CALORIE TRACKER
# -------------------------------------------------------
elif tab == "🔥 Calorie Tracker":
    st.header("🔥 Calorie Tracker")

    if not st.session_state.get("is_premium", False):
        st.warning("🔒 This feature is for Premium Members.")
    else:
        foods = {
            "Roti": (300, 8, 55),
            "Rice": (130, 2.7, 28),
            "Paneer": (265, 18, 6),
            "Egg": (155, 13, 1.1),
            "Milk": (60, 3.2, 5),
            "Soya Chunks": (345, 52, 33),
            "Oats": (380, 13, 67),
            "Banana": (89, 1.1, 23),
            "Apple": (52, 0.3, 14),
            "Peanuts": (567, 25, 16),
        }
        food = st.selectbox("🍽️ Choose food:", list(foods.keys()))
        qty = st.number_input("Quantity (grams)", 1, 1000, 100)
        cal, p, c = foods[food]
        st.markdown(f"**Calories:** {(cal/100)*qty:.1f} kcal | **Protein:** {(p/100)*qty:.1f} g | **Carbs:** {(c/100)*qty:.1f} g")


# -------------------------------------------------------
# 🤖 CHATBOT
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
# 💳 PREMIUM SECTION
# -------------------------------------------------------
elif tab == "💳 Premium":
    st.header("💳 Unlock FIT PRO Premium (₹299 / Year)")

    user_email = st.text_input("📧 Enter your email:")
    if user_email.strip() == "":
        st.warning("⚠️ Please enter your email first.")
    else:
        plan_type = get_plan_type(user_email)
        if plan_type == "Premium":
            st.success("🎉 You are already Premium!")
        else:
            st.info("💡 You are currently on Basic Plan.")
            st.markdown("""
            💰 **FIT PRO Premium – ₹299 / Year**
            🔓 Unlock features:
            - Advanced Workout Plans  
            - Indian Diet Generator  
            - Calorie Tracker  
            - Smart Chatbot Assistant  
            """)
            payment_link = "https://rzp.io/rzp/peRgfyS"
            st.markdown(f"[🛒 Pay ₹299 on Razorpay]({payment_link})", unsafe_allow_html=True)

            payment_id = st.text_input("💳 Enter your Payment ID:")
            if st.button("✅ Verify & Activate Premium"):
                if payment_id.startswith("pay_"):
                    add_or_update_user(user_email, "Premium", payment_id)
                    st.session_state["is_premium"] = True
                    st.success("🎉 Payment verified! Premium access granted for 1 year.")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Invalid Payment ID.")

    st.markdown("---")
    st.caption("💗 Designed by Harsh | Made with 💖 for Students & Fitness Lovers IN")
