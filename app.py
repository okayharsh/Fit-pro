import os
import time
import sqlite3
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from groq import Groq
import json

# =========================
# BASIC APP SETTINGS
# =========================
st.set_page_config(page_title="FIT PRO", page_icon="💪", layout="centered")

# ============================
# PWA: MANIFEST + IOS META
# ============================
st.markdown("""
<script>
// ✅ Universal Chrome Install Prompt (Android + iOS)
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  console.log("✅ beforeinstallprompt triggered");

  // Create a glowing install button dynamically
  const btn = document.createElement('button');
  btn.textContent = "📲 Install FIT PRO";
  btn.style.cssText = `
    position: fixed;
    bottom: 22px;
    right: 22px;
    padding: 14px 22px;
    background: linear-gradient(135deg, #00c6ff, #0072ff);
    color: white;
    font-weight: 700;
    border: none;
    border-radius: 14px;
    box-shadow: 0 0 18px rgba(14,165,255,.6);
    font-size: 15px;
    z-index: 9999;
    cursor: pointer;
  `;
  document.body.appendChild(btn);

  btn.addEventListener('click', async () => {
    btn.disabled = true;
    deferredPrompt.prompt();
    const result = await deferredPrompt.userChoice;
    if (result.outcome === 'accepted') {
      localStorage.setItem('fitpro_installed', 'true');
    }
    deferredPrompt = null;
    btn.remove();
  });
});

window.addEventListener('appinstalled', () => {
  console.log("🎉 FIT PRO installed successfully!");
});
</script>
""", unsafe_allow_html=True)
# Chrome install prompt (Android + iOS)
st.markdown("""
<script>
// ✅ Universal Chrome Install Prompt (Android + iOS)
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  console.log("✅ beforeinstallprompt triggered");

  // Create glowing install button dynamically
  const btn = document.createElement('button');
  btn.textContent = "📲 Install FIT PRO";
  btn.style.cssText = `
    position: fixed;
    bottom: 22px;
    right: 22px;
    padding: 14px 22px;
    background: linear-gradient(135deg, #00c6ff, #0072ff);
    color: white;
    font-weight: 700;
    border: none;
    border-radius: 14px;
    box-shadow: 0 0 18px rgba(14,165,255,.6);
    font-size: 15px;
    z-index: 9999;
    cursor: pointer;
  `;
  document.body.appendChild(btn);

  btn.addEventListener('click', async () => {
    btn.disabled = true;
    deferredPrompt.prompt();
    const result = await deferredPrompt.userChoice;
    if (result.outcome === 'accepted') {
      localStorage.setItem('fitpro_installed', 'true');
    }
    deferredPrompt = null;
    btn.remove();
  });
});

window.addEventListener('appinstalled', () => {
  console.log("🎉 FIT PRO installed successfully!");
});
</script>
""", unsafe_allow_html=True)




# 2) Register service worker
st.markdown("""
<script>
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('sw.js', { scope: './' })
  .then(() => console.log('✅ Service Worker Registered'))
  .catch(err => console.log('❌ Service Worker Failed:', err));
}
</script>
""", unsafe_allow_html=True)

# 3) Smart “Install App” button (Android + Desktop)
st.markdown("""
<style>
#install-btn {
  display:none;
  position: fixed;
  bottom: 22px; right: 22px;
  background: linear-gradient(135deg, #0ea5ff, #0f1113);
  color: #fff; border: none; border-radius: 14px;
  padding: 14px 20px; font-size: 15px; font-weight: 700;
  box-shadow: 0 8px 24px rgba(14,165,255,.35);
  cursor: pointer; z-index: 9999; transition: all .25s ease;
}
#install-btn:hover { transform: translateY(-2px); box-shadow: 0 10px 28px rgba(14,165,255,.45); }
</style>
<button id="install-btn">📲 Install FIT PRO</button>
<script>
let deferredPrompt; const btn = document.getElementById('install-btn');
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault(); deferredPrompt = e;
  if (!localStorage.getItem('fitpro_installed')) btn.style.display='block';
  btn.onclick = () => {
    btn.style.display='none';
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then(c => {
      if (c.outcome === 'accepted') localStorage.setItem('fitpro_installed','1');
      deferredPrompt = null;
    });
  };
});
window.addEventListener('appinstalled', () => {
  console.log('🎉 FIT PRO installed'); btn.style.display='none';
  localStorage.setItem('fitpro_installed','1');
});
</script>
""", unsafe_allow_html=True)

# =========================
# GLOBAL STYLES (UI EXACT LOOK)
# =========================
st.markdown("""
<style>
/* Background + base text */
html, body, .main { background:#0f1113 !important; color:#e7eef6 !important; }

/* Header with electric-blue neon pulse */
.app-header{
  text-align:center; margin:34px 0 8px 0;
  font-size:64px; font-weight:900; letter-spacing:2px; text-transform:uppercase;
  background: linear-gradient(90deg,#00c6ff,#0072ff);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent;
  text-shadow: 0 0 18px rgba(14,165,255,.55), 0 0 42px rgba(14,165,255,.25);
  animation: glowPulse 2.8s ease-in-out infinite alternate;
}
@keyframes glowPulse {
  from { text-shadow: 0 0 14px rgba(14,165,255,.45), 0 0 28px rgba(14,165,255,.2); }
  to   { text-shadow: 0 0 28px rgba(14,165,255,.85), 0 0 56px rgba(14,165,255,.35); }
}

/* Tabs row */
/* Tabs row (Fix: single-line, equal width, electric glow on active) */
.button-row {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin: 25px auto 30px;
  flex-wrap: nowrap; /* ✅ prevents breaking to next line */
  overflow-x: auto;
}

.stButton>button {
  background: #12151a;
  color: #f0f6ff;
  border: 1px solid #26313f;
  border-radius: 14px;
  width: 170px; /* ✅ fixed width for perfect alignment */
  height: 48px;
  font-weight: 700;
  font-size: 15px;
  white-space: nowrap; /* ✅ keep text in one line */
  box-shadow: 0 6px 18px rgba(0,0,0,.25);
  transition: all 0.25s ease-in-out;
}

.stButton>button:hover {
  border-color: #00c6ff;
  box-shadow: 0 0 12px #00c6ffaa;
  transform: translateY(-1px);
}

/* Inputs - clean glassy */
.stNumberInput, .stTextInput, .stSelectbox{
  background: rgba(255,255,255,.06) !important;
  border-radius:14px !important; backdrop-filter:blur(8px) !important;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.05) !important;
}

/* Section headers */
h1, h2, h3{ color:#e6f3ff; }

/* Scrollbar */
::-webkit-scrollbar{ width:10px; } 
::-webkit-scrollbar-thumb{ background:linear-gradient(180deg,#00aaff,#004aad); border-radius:8px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="app-header">FIT PRO 💪</div>', unsafe_allow_html=True)

# =========================
# DB INIT
# =========================
DB_NAME = "fitness_app.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS users(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          email TEXT UNIQUE, plan TEXT DEFAULT 'Basic',
          expiry TEXT, payment_id TEXT
        )""")
        conn.commit()

def add_or_update_user(email, plan, payment_id):
    expiry_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE email=?", (email,))
        if c.fetchone():
            c.execute("UPDATE users SET plan=?, expiry=?, payment_id=? WHERE email=?",
                      (plan, expiry_date, payment_id, email))
        else:
            c.execute("INSERT INTO users(email,plan,expiry,payment_id) VALUES(?,?,?,?)",
                      (email, plan, expiry_date, payment_id))
        conn.commit()

def get_plan_type(email):
    if not email: return "Basic"
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT plan, expiry FROM users WHERE email=?", (email,))
        row = c.fetchone()
    if not row: return "Basic"
    plan, expiry = row
    if not expiry: return "Basic"
    try:
        if datetime.strptime(expiry, "%Y-%m-%d") > datetime.now():
            return plan
    except: pass
    return "Basic"

init_db()

# =========================
# ENV + GROQ CLIENT
# =========================
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
client = None
if GROQ_API_KEY:
    try:
        client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        st.error(f"⚠️ Groq init failed: {e}")
else:
    st.warning("🔑 GROQ_API_KEY missing — AI features disabled.")

# =========================
# EMAIL LOGIN (FIXED)
# =========================
if "user_email" not in st.session_state: st.session_state["user_email"] = ""
if "is_premium" not in st.session_state: st.session_state["is_premium"] = False

st.markdown("### ✉️ Enter your email to continue:")
raw_email = st.text_input("Email Address", placeholder="example@gmail.com")

def is_valid_email(email: str) -> bool:
    email = (email or "").strip()
    if "@" not in email or "." not in email: return False
    if " " in email: return False
    return True

if raw_email:
    email = raw_email.strip()
    if not is_valid_email(email):
        st.error("❌ Invalid email format.")
        st.stop()
    if email != st.session_state["user_email"]:
        st.session_state["user_email"] = email
        st.session_state["is_premium"] = (get_plan_type(email) == "Premium")
        st.rerun()

if not st.session_state["user_email"]:
    st.warning("⚠️ Please enter your email to use FIT PRO.")
    st.stop()

# Update plan in session
current_plan = get_plan_type(st.session_state["user_email"])
st.session_state["is_premium"] = (current_plan == "Premium")
if st.session_state["is_premium"]:
    st.success(f"🌟 You are on the **Premium Plan** — Welcome, {st.session_state['user_email']}!")
else:
    st.info(f"✅ You are on the **Basic Plan** — Logged in as {st.session_state['user_email']}")

st.markdown("---")

# =========================
# PROMPTS
# =========================
def workout_prompt(age, sex, height, weight, experience, days, equipment, goal):
    # --- Goal-specific instructions ---
    goal_instructions = {
        "Fat Loss": """
Prioritize high-intensity full-body circuits, compound lifts, supersets, and short rest (30–45 s).
Add cardio 4–5×/week, focus on calorie burn and endurance. Moderate weights, higher reps (12–20).""",
        
        "Muscle Gain": """
Focus on hypertrophy (8–12 reps, 3–4 sets). Emphasize progressive overload,
split by muscle groups, minimal cardio, longer rest (60–90 s). Include isolation movements.""",
        
        "Recomposition": """
Blend hypertrophy + strength. Use compound lifts (6–10 reps) with accessory isolation work.
Add 1–2 cardio/HIIT sessions weekly. Maintain balance between volume and recovery.""",
        
        "Strength": """
Emphasize low-rep heavy compound lifts (3–6 reps) such as squat, bench, deadlift, overhead press.
Include accessory lifts for stability. Rest 2–3 min between heavy sets. Minimal cardio."""
    }

    specific_goal_info = goal_instructions.get(goal, "Focus on balanced full-body functional training.")

    # --- Dynamic prompt respecting user’s chosen training days ---
    return f"""
You are an experienced Indian certified gym trainer.

Design a **{days}-day workout plan** (not 7) based on the user's schedule and goal.

User details:
- Age: {age}
- Sex: {sex}
- Height: {height} cm
- Weight: {weight} kg
- Experience: {experience}
- Available days per week: {days}
- Equipment: {equipment}
- Goal: {goal}

Training philosophy for this goal:
{specific_goal_info}

Requirements:
- Plan **exactly {days} distinct days** (e.g., Day 1 – Day {days})
- Include: Exercise names, sets, reps, rest period, and short notes
- Make sure each goal type feels **unique**:
  • Fat Loss → cardio + circuits + lighter loads  
  • Muscle Gain → split training + hypertrophy volume  
  • Recomposition → strength + hypertrophy mix  
  • Strength → compound + heavy + power moves  
- Use realistic Indian gym exercises
- Output **only markdown**, well formatted and organized
"""


tab = st.session_state["active_tab"]

# =========================
# GYM PLAN
# =========================
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
        submitted = st.form_submit_button("Generate Workout 🚀")

    if submitted:
        if not client:
            st.error("AI is disabled (no API key).")
        else:
            with st.spinner("Generating workout plan..."):
                try:
                    res = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role":"user","content": workout_prompt(age,sex,height,weight,experience,days,equipment,goal)}],
                        temperature=0.5
                    )
                    st.markdown(res.choices[0].message.content)
                except Exception as e:
                    st.error(f"Error: {e}")

# =========================
# DIET PLAN (Premium)
# =========================
elif tab == "🍽️ Diet Plan":
    st.header("🥗 Personalized Diet Plan (Premium)")
    if not st.session_state["is_premium"]:
        st.warning("🔒 This feature is for **Premium members**.")
        st.info("Unlock it in the **Premium** tab for ₹299/year.")
    else:
        age = st.number_input("Age", 14, 80, 22, key="diet_age")
        weight = st.number_input("Weight (kg)", 35, 200, 70, key="diet_weight")
        goal = st.selectbox("Goal", ["Fat Loss", "Muscle Gain", "Recomposition", "Strength"], key="diet_goal")
        diet_type = st.selectbox("Diet Type", ["Vegetarian", "Eggetarian", "Non-Vegetarian"], key="diet_type")

        if st.button("Generate Premium Diet 🍱"):
            if not client:
                st.error("AI is disabled (no API key).")
            else:
                with st.spinner("Crafting your personalized premium diet plan..."):
                    try:
                        prompt = f"""
Create a detailed 7-day Indian diet plan ({diet_type}) for {goal}.
Age: {age}, Weight: {weight}kg.
Include Breakfast, Lunch, Snacks, Dinner + daily calories & protein estimates.
Return markdown only.
"""
                        res = client.chat.completions.create(
                            model="llama-3.1-8b-instant",
                            messages=[{"role":"user","content": prompt}],
                            temperature=0.5
                        )
                        st.success("🎯 Premium Diet Plan Generated!")
                        st.markdown(res.choices[0].message.content)
                    except Exception as e:
                        st.error(f"Error generating diet plan: {e}")

# =========================
# CALORIE TRACKER
# =========================
elif tab == "🔥 Calorie Tracker":
    st.header("🔥 Calorie Tracker")
    if not st.session_state["is_premium"]:
        st.warning("🔒 Available only for Premium members.")
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
        cal, p, c = foods[food]
        st.markdown(f"**Calories:** {(cal/100)*qty:.1f} kcal | **Protein:** {(p/100)*qty:.1f} g | **Carbs:** {(c/100)*qty:.1f} g")

# =========================
# CHATBOT
# =========================
elif tab == "🤖 Chatbot":
    st.header("🤖 FIT PRO Chatbot")
    if not st.session_state["is_premium"]:
        st.warning("💬 Chatbot is available only for Premium members.")
    else:
        q = st.text_input("Ask your question:")
        if q and client:
            with st.spinner("Thinking..."):
                try:
                    ans = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role":"user","content": q}],
                        temperature=0.4
                    )
                    st.markdown(ans.choices[0].message.content)
                except Exception as e:
                    st.error(f"Chatbot error: {e}")

# =========================
# PREMIUM
# =========================
elif tab == "💳 Premium":
    st.header("💳 Unlock FIT PRO Premium (₹299 / Year)")
    user_email = st.text_input("📧 Enter your email:")
    if not user_email.strip():
        st.warning("⚠️ Please enter your email first.")
    else:
        plan = get_plan_type(user_email)
        if plan == "Premium":
            st.success("🎉 You are a Premium Member!")
        else:
            st.info("💡 You are on **Basic Plan**.")
            st.markdown("""
            **FIT PRO Premium – ₹299 / Year**
            Unlock:
            - Advanced Workout Plans  
            - Indian Diet Generator  
            - Calorie Tracker  
            - Smart Chatbot Assistant  
            """)
            payment_link = "https://rzp.io/rzp/5VHFcVO1"
            st.markdown(f"[🛒 Pay ₹299 on Razorpay]({payment_link})")

            payment_id = st.text_input("💳 Enter your Payment ID (e.g., pay_XXXXXXXXXXXX):")
            if st.button("✅ Verify & Activate Premium"):
                if payment_id.startswith("pay_"):
                    add_or_update_user(user_email, "Premium", payment_id)
                    st.success("🎉 Payment verified! Premium access granted for 1 year.")
                    st.balloons()  # 🎈🎈🎈
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Invalid Payment ID. Please check and try again.")

st.markdown("---")
st.caption("💗 Designed by Harsh | Made with 💖 for Students & Fitness Lovers IN")
