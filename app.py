import streamlit as st
import sqlite3
from groq import Groq
from datetime import datetime, timedelta
import pandas as pd
import time
import os
from dotenv import load_dotenv
load_dotenv()


# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="FIT PRO", page_icon="💪", layout="centered")

st.markdown("""
    <style>
        .stButton>button {
            background-color: #ff2e2e; color: white; font-weight: bold; border-radius: 8px;
        }
        .summary-box {
            background-color: #f5f5f5; border-radius: 10px; padding: 10px;
            border: 1px solid #ddd; margin-top: 10px;
        }
        .unlock-btn {
            background-color:#ff2e2e; color:#fff; padding:8px 12px; border-radius:8px; text-decoration:none;
            font-weight:bold;
        }
    </style>
""", unsafe_allow_html=True)

# ------------------ KEYS & LINKS ------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
RAZORPAY_PAGE_URL = "https://rzp.io/rzp/ci6Oh3C"


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)


# ------------------ DATABASE ------------------
with sqlite3.connect("fitness_app.db") as conn:
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            plan TEXT,
            expiry TEXT,
            payment_id TEXT
        )
    """)
    conn.commit()

# ------------------ HELPERS ------------------
def add_user(name, plan, payment_id):
    expiry_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    conn = sqlite3.connect("fitness_app.db")
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE name=?", (name,))
    if c.fetchone():
        c.execute("UPDATE users SET plan=?, expiry=?, payment_id=? WHERE name=?", (plan, expiry_date, payment_id, name))
    else:
        c.execute("INSERT INTO users (name, plan, expiry, payment_id) VALUES (?, ?, ?, ?)",
                  (name, plan, expiry_date, payment_id))
    conn.commit()
    conn.close()

def get_plan_type(name):
    if not name:
        return "Basic"
    conn = sqlite3.connect("fitness_app.db")
    c = conn.cursor()
    c.execute("SELECT plan, expiry FROM users WHERE name=?", (name,))
    result = c.fetchone()
    conn.close()
    if not result:
        return "Basic"
    plan, expiry = result
    if not expiry:
        return "Basic"
    try:
        exp_dt = datetime.strptime(expiry, "%Y-%m-%d")
        if exp_dt > datetime.now():
            return plan
    except:
        return "Basic"
    return "Basic"

# ------------------ PROMPTS ------------------
def workout_prompt(age, sex, height, weight, experience, days, equipment, goal):
    return f"""
You are an Indian certified gym trainer.
Create a 7-day workout plan for:
Age: {age}, Sex: {sex}, Height: {height} cm, Weight: {weight} kg
Experience: {experience}, Days: {days}, Equipment: {equipment}, Goal: {goal}

Rules:
- Give day-wise exercises aligned with goal.
- Include sets, reps, rest.
- Example: For fat loss → more HIIT, circuit, supersets.
  For muscle gain → hypertrophy, 8–12 reps, progressive overload.
  For recomposition → mix both.
  For strength → low reps, high load, compound lifts.
Return only the workout plan in markdown.
"""

def diet_prompt(age, weight, goal, diet_type):
    return f"""
You are an Indian nutritionist.
Create a 7-day Indian student-friendly diet plan for:
Age: {age}, Weight: {weight} kg, Goal: {goal}, Diet Type: {diet_type}

Rules:
- 100% Indian meals (roti, dal, rice, paneer, etc.)
- Each day: breakfast, lunch, dinner, snacks + approximate calories.
- Keep meals budget-friendly (₹250/day max).
- Align calorie goal with goal type.
Return only the diet in markdown.
"""

# ------------------ UI ------------------
st.title("💪 FIT PRO")
st.markdown("Your Personal Gym + Diet Assistant (Indian Edition 🇮🇳)")

name = st.text_input("Enter your email (required for Premium access):")
plan_type = get_plan_type(name) if name else "Basic"

if name:
    if plan_type != "Basic":
        st.success(f"Welcome back, {name}! Premium active ✅")
    else:
        st.info("You're currently on the Basic (Free) plan.")
else:
    st.info("Enter your email to access or purchase Premium.")

tabs = ["🏋️ Gym Plan", "🍽️ Diet Plan", "🔥 Calorie Tracker", "🤖 Chatbot", "💳 Premium"]
tab = st.radio("Navigation", tabs, horizontal=True, label_visibility="collapsed")

# ------------------ GYM PLAN (only workout) ------------------
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
        if not name:
            st.error("⚠️ Please enter your email first!")
        else:
            with st.spinner("Generating workout plan..."):
                try:
                    workout_res = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": workout_prompt(age, sex, height, weight, experience, days, equipment, goal)}],
                        temperature=0.5,
                        max_tokens=2500
                    )
                    workout_md = workout_res.choices[0].message.content
                    st.markdown(workout_md)
                except Exception as e:
                    st.error(f"Error generating workout: {e}")

# ------------------ DIET PLAN (separate) ------------------
elif tab == "🍽️ Diet Plan":
    st.header("Generate Diet Plan")
    if not name:
        st.error("⚠️ Please enter your email to continue.")
    else:
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
                        temperature=0.5,
                        max_tokens=2500
                    )
                    st.markdown(res.choices[0].message.content)
                except Exception as e:
                    st.error(f"Error generating diet: {e}")

# ------------------ CALORIE TRACKER ------------------
elif tab == "🔥 Calorie Tracker":
    st.header("🔥 Calorie Tracker (per 100g basis)")
    if get_plan_type(name) != "Premium":
        st.warning("🔒 Premium users only.")
    else:
        foods = {
            "Roti": (300, 8, 55),
            "Rice": (130, 2.7, 28),
            "Dal": (120, 9, 15),
            "Paneer": (265, 18, 6),
            "Egg": (155, 13, 1.1),
            "Milk": (60, 3.2, 5),
            "Soya Chunks": (345, 52, 33),
            "Poha": (130, 2.5, 27),
            "Upma": (140, 3.4, 25),
            "Oats": (380, 13, 67),
            "Idli": (110, 3.2, 20),
            "Dosa": (165, 3.9, 31),
            "Bread": (265, 9, 49),
            "Rajma": (140, 9, 25),
            "Chole": (150, 8, 27),
            "Paratha": (300, 7, 45),
            "Aloo Sabzi": (120, 2, 18),
            "Apple": (52, 0.3, 14),
            "Orange": (47, 0.9, 12),
            "Peanuts": (567, 25, 16),
            "Almonds": (579, 21, 22),
            "Khichdi": (120, 5, 20),
            "Curd": (98, 11, 4),
            "Tofu": (120, 13, 3),
            "Bhindi": (80, 2.6, 7),
            "Mixed Veg": (90, 3, 12),
            "Palak Paneer": (200, 14, 10),
            "Dal Tadka": (180, 10, 15),
            "Pulao": (150, 4, 25),
            "Chapati": (270, 9, 48),
            "Maggi": (365, 10, 56),
            "Aloo Paratha": (280, 6, 45),
            "Tea": (40, 1, 5),
            "Coffee": (50, 1, 6),
            "Green Tea": (2, 0, 0),
            "Sprouts": (90, 7, 15),
            "Sandwich": (250, 9, 35),
            "Pav Bhaji": (450, 9, 40),
            "Biryani": (290, 6, 45),
            "Vegetable Soup": (60, 2, 10)
        }

        selected_food = st.selectbox("🍽️ Choose a food item:", list(foods.keys()))
        quantity = st.number_input("⚖️ Enter quantity (in grams):", min_value=1, max_value=1000, value=100)

        if selected_food and quantity:
            cal, protein, carbs = foods[selected_food]
            calories = (cal / 100) * quantity
            protein_amt = (protein / 100) * quantity
            carbs_amt = (carbs / 100) * quantity

            st.markdown(f"""
            ### 🍛 **Nutrition Info for {quantity}g {selected_food}:**
            - **Calories:** {calories:.1f} kcal  
            - **Protein:** {protein_amt:.1f} g  
            - **Carbs:** {carbs_amt:.1f} g
            """)

        if st.checkbox("📊 Show all food items (per 100g)"):
            df = pd.DataFrame(foods, index=["Calories", "Protein", "Carbs"]).T
            st.dataframe(df)

# ------------------ CHATBOT ------------------
elif tab == "🤖 Chatbot":
    if get_plan_type(name) != "Premium":
        st.warning("💬 Available only for Premium users.")
    else:
        st.header("🤖 FIT PRO Chatbot")
        q = st.text_input("Ask your fitness/diet question:")
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
                    st.error(f"Error from Chatbot: {e}")

# ------------------ PREMIUM ------------------
elif tab == "💳 Premium":
    st.header("💳 Unlock FIT PRO Premium (₹299 / 1 Year)")
    if not name:
        st.error("⚠️ Please enter your email first.")
    else:
        if get_plan_type(name) == "Premium":
            st.success("🎉 You already have Premium access.")
        st.markdown(
            f'<a class="unlock-btn" href="{RAZORPAY_PAGE_URL}" target="_blank">UNLOCK PREMIUM — Pay ₹299</a>',
            unsafe_allow_html=True,
        )
        st.info("After payment, paste the Razorpay Payment ID (starts with pay_):")
        payment_id = st.text_input("Enter Razorpay Payment ID:", key="razorpay_id")
        if st.button("✅ Verify & Activate Premium"):
            if payment_id.strip() == "":
                st.error("⚠️ Please enter Razorpay Payment ID.")
            elif not payment_id.lower().startswith("pay_"):
                st.error("❌ Invalid Razorpay Payment ID.")
            else:
                try:
                    add_user(name, "Premium", payment_id)
                    st.success("🎉 Premium unlocked for 1 year! Refreshing...")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error activating Premium: {e}")

st.markdown("---")
st.caption("🧠 Design by Harsh | Made with ❤️ for students & fitness lovers.")
