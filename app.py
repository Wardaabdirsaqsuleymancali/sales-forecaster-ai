import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestRegressor
import sqlite3
import hashlib
from datetime import datetime

# 1. Page Config Setup
st.set_page_config(page_title="Universal Enterprise AI Forecaster", layout="wide")

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS tab1_forecast_history 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT,
                  business_type TEXT,
                  category TEXT,
                  branch TEXT,
                  price REAL,
                  promo TEXT,
                  season TEXT,
                  days INTEGER,
                  total_stock INTEGER,
                  total_revenue REAL,
                  date_saved TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS custom_forecast_history 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT,
                  business_type TEXT,
                  target_column TEXT,
                  features TEXT,
                  predicted_value REAL,
                  date_saved TEXT)''')
    conn.commit()
    
    c.execute("SELECT * FROM users WHERE username=?", ('admin',))
    if not c.fetchone():
        hashed_admin_p = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT INTO users VALUES (?, ?)", ('admin', hashed_admin_p))
        conn.commit()
    conn.close()

def add_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    hashed_p = hashlib.sha256(password.encode()).hexdigest()
    try:
        c.execute("INSERT INTO users VALUES (?, ?)", (username, hashed_p))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False 
    conn.close()
    return success

def check_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    hashed_p = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_p))
    result = c.fetchone()
    conn.close()
    return result is not None

def save_tab1_forecast(username, b_type, cat, branch, price, promo, season, days, stock, revenue):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''INSERT INTO tab1_forecast_history 
                 (username, business_type, category, branch, price, promo, season, days, total_stock, total_revenue, date_saved)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
              (username, b_type, cat, branch, float(price), promo, season, int(days), int(stock), float(revenue), now))
    conn.commit()
    conn.close()

def get_tab1_forecast_history(username, b_type, lang_dict):
    conn = sqlite3.connect('users.db')
    df = pd.read_sql_query('''SELECT date_saved, category, branch, price, promo, season, days, total_stock, total_revenue 
                             FROM tab1_forecast_history 
                             WHERE username=? AND business_type=? 
                             ORDER BY id DESC''', conn, params=(username, b_type))
    conn.close()
    
    if not df.empty:
        df.columns = [
            lang_dict["hist_date"], lang_dict["hist_cat"], lang_dict["hist_branch"],
            lang_dict["hist_price"], lang_dict["hist_promo"], lang_dict["hist_season"],
            lang_dict["hist_days"], lang_dict["hist_stock_res"], lang_dict["hist_rev_res"]
        ]
    return df

def save_custom_forecast(username, b_type, target, features, value):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''INSERT INTO custom_forecast_history (username, business_type, target_column, features, predicted_value, date_saved)
                 VALUES (?, ?, ?, ?, ?, ?)''', (username, b_type, target, features, float(value), now))
    conn.commit()
    conn.close()

def get_custom_forecast_history(username, b_type, lang_dict):
    conn = sqlite3.connect('users.db')
    df = pd.read_sql_query('''SELECT date_saved, target_column, features, predicted_value 
                             FROM custom_forecast_history 
                             WHERE username=? AND business_type=? 
                             ORDER BY id DESC''', conn, params=(username, b_type))
    conn.close()
    
    if not df.empty:
        df.columns = [
            lang_dict["hist_date"], lang_dict["hist_target"], lang_dict["hist_features"], lang_dict["hist_pred_val"]
        ]
    return df

init_db()

# --- MULTI-LANGUAGE DICTIONARY ---
translations = {
    "English": {
        "title": "🤖 UNIVERSAL BUSINESS AI FORECASTER",
        "welcome": "Welcome back",
        "login_title": "Create your account / Sign In",
        "login_desc": "Please choose your preferred login mode.",
        "mode_login": "Soo Gal (Login)",
        "mode_signup": "Is-diwaangeli (Sign Up)",
        "username": "Username",
        "password": "Password",
        "new_username": "New Username",
        "new_password": "New Password",
        "btn_login": "Sign In",
        "btn_signup": "Sign Up",
        "logout": "🔐 Log Out",
        "biz_selection": "## 🏢 BUSINESS SELECTION",
        "biz_label": "Select business type:",
        "tab1_name": "📊 PRE-TRAINED AI MODEL",
        "tab2_name": "🏋️‍♂️ TRAIN AI WITH YOUR CSV DATA",
        "config_title": "### ⚙️ FORECAST CONFIGURATION (BUILT-IN AI MODEL)",
        "cat_label": "📦 Select Category",
        "branch_label": "🏢 Store Branch Name",
        "price_label": "💵 Average Item Price ($)",
        "promo_label": "📢 Is Promotion Active?",
        "promo_no": "No Promo",
        "promo_yes": "Active Promo",
        "days_label": "📅 Forecast Duration",
        "season_label": "🌤️ Seasonal Impact",
        "btn_run": "🚀 START AI FORECAST",
        "rev_metric": "💰 REVENUE (AI Prediction)",
        "stock_metric": "📦 STOCK DEMAND",
        "avg_metric": "📈 AVG DAILY SALES",
        "graph_title": "AI Forecast for Category",
        "btn_save": "💾 SAVE FORECAST DATA",
        "hist_title": "📋 PAST FORECAST HISTORY",
        "hist_info": "ℹ️ No past forecast history found for this business.",
        "success_save": "✅ Forecast data successfully saved to history!",
        "csv_title": "📁 Upload Your Custom CSV Data",
        "csv_label": "Choose Training File (CSV File):",
        "csv_success": "✅ Data successfully read!",
        "target_label": "🎯 Select Target Column:",
        "features_label": "⚙️ Select Features:",
        "btn_train": "🚀 START TRAINING CUSTOM AI MODEL",
        "train_spinner": "AI is learning your data...",
        "train_success": "🎉 Custom AI Model trained successfully!",
        "custom_predict_title": "🔮 Make Predictions with Custom Model",
        "custom_mode_label": "🔄 Choose data entry mode:",
        "mode_manual": "Manual entry",
        "mode_csv": "Upload another future CSV file",
        "btn_calc_custom": "CALCULATE CUSTOM FORECAST",
        "metric_custom_res": "Custom Prediction Result",
        "btn_predict_file": "🤖 AI: PREDICT ENTIRE FILE",
        "file_pred_success": "✅ File prediction completed!",
        "graph_custom_title": "Custom Prediction Chart per Row",
        "custom_hist_title": "📋 CUSTOM FORECAST HISTORY",
        "custom_hist_info": "ℹ️ No custom forecast history found.",
        # Table Columns
        "hist_date": "Date Saved", "hist_cat": "Category", "hist_branch": "Branch",
        "hist_price": "Price ($)", "hist_promo": "Promotion", "hist_season": "Season",
        "hist_days": "Duration", "hist_stock_res": "Predicted Stock", "hist_rev_res": "Predicted Revenue ($)",
        "hist_target": "Target Column", "hist_features": "Features Used", "hist_pred_val": "Prediction Result"
    },
    "Soomaali": {
        "title": "🤖 UNIVERSAL BUSINESS AI FORECASTER",
        "welcome": "Koodhka waxaa maamulaya",
        "login_title": "Abuur Koonto / Soo Gal",
        "login_desc": "Fadlan dooro habka aad rabto inaad u gasho nidaamka.",
        "mode_login": "Soo Gal (Login)",
        "mode_signup": "Is-diwaangeli (Sign Up)",
        "username": "Username (Magacaaga)",
        "password": "Password (Sirtaada)",
        "new_username": "Magac Cusub",
        "new_password": "Sir Cusub",
        "btn_login": "Sign In",
        "btn_signup": "Sign Up",
        "logout": "🔐 Log Out (Ka Bax)",
        "biz_selection": "## 🏢 DOORASHADA GANACSIGA",
        "biz_label": "Dooro nooca ganacosiga:",
        "tab1_name": "📊 MODEL-KII HORE EE DIYAARKA AH",
        "tab2_name": "🏋️‍♂️ U TABABAR AI-GA XOGTAADA CSV",
        "config_title": "### ⚙️ QAABAYNTA XOGTA SAADAASHA (BUILT-IN AI MODEL)",
        "cat_label": "📦 Dooro Qaybta Alaabta (Category)",
        "branch_label": "🏢 Magaca Faraca/Dukaanka",
        "price_label": "💵 Celceliska Qiimaha Alaabta ($)",
        "promo_label": "📢 Qiimo Dhimis Ma Jiraa (Promotion)?",
        "promo_no": "Maya (No Promo)",
        "promo_yes": "Haa (Active Promo)",
        "days_label": "📅 Muddada Saadaasha",
        "season_label": "🌤️ Saamaynta Xilliga",
        "btn_run": "🚀 BILAABO SAADAASHA",
        "rev_metric": "💰 REVENUE (AI Prediction)",
        "stock_metric": "📦 STOCK DEMAND",
        "avg_metric": "📈 AVG DAILY SALES",
        "graph_title": "Saadaasha AI ee Qaybta",
        "btn_save": "💾 SAVE FORECAST DATA (KAYDI)",
        "hist_title": "📋 TAARIIKHDA SAADAASHII HORE",
        "hist_info": "ℹ️ Weligaa wax saadaal ah ma aad kaydsan oo ku saabsan ganacsigaan.",
        "success_save": "✅ Natiijadii saadaasha si guul leh ayaa loo kaydiyey taariikhda!",
        "csv_title": "📁 Soo Geli Xogta weyn ee Custom-ka ah",
        "csv_label": "Dooro Faylka Tababarka (CSV File):",
        "csv_success": "✅ Xogtii si guul leh ayaa loo soo akhriyey!",
        "target_label": "🎯 Dooro tiirka ah Target-ka:",
        "features_label": "⚙️ Dooro tiirarka (Features):",
        "btn_train": "🚀 BILOW TABABARKA MODEL-KA CUSTOM-KA AH",
        "train_spinner": "AI-ga ayaa hadدا baranaya...",
        "train_success": "🎉 AI Custom Model-kii guul ayuu ku bartay xogtaada!",
        "custom_predict_title": "🔮 Ku Samee Saadaal Model-kaagii Custom-ka ahaa",
        "custom_mode_label": "🔄 Dooro qaabka xogta:",
        "mode_manual": "Gacanta ku geli xog yar",
        "mode_csv": "Fayl CSV kale oo mustaqbalka ah soo geli",
        "btn_calc_custom": "XISSAABI SAADAASHA CUSTOM-KA AH",
        "metric_custom_res": "Natiijada Saadaasha Custom-ka ah",
        "btn_predict_file": "🤖 AI: SAADAALI FAYLKAN OO DHAN",
        "file_pred_success": "✅ Saadaashii falka CSV waa dhammaystirmay!",
        "graph_custom_title": "Garaafka Saadaasha Cusub ee Row kasta",
        "custom_hist_title": "📋 TAARIIKHDA SAADAASHII CUSTOM-KA AH",
        "custom_hist_info": "ℹ️ Ma jirto taariikh saadaal custom ah oo hore loogu sameeyay.",
        # Table Columns
        "hist_date": "Taariikhda", "hist_cat": "Qaybta Alaabta", "hist_branch": "Faraca",
        "hist_price": "Qiimaha ($)", "hist_promo": "Promotion", "hist_season": "Xilliga",
        "hist_days": "Muddada", "hist_stock_res": "Tirada Saadaasha", "hist_rev_res": "Dakhliga ($)",
        "hist_target": "Target-ka", "hist_features": "Tiirarka (Features)", "hist_pred_val": "Natiijada Saadaasha"
    },
    "Arabic": {
        "title": "🤖 متنبئ الذكاء الاصطناعي الشامل للشركات",
        "welcome": "مرحباً بك مجدداً",
        "login_title": "إنشاء حساب / تسجيل الدخول",
        "login_desc": "يرجى اختيار طريقة الدخول المفضلة لديك.",
        "mode_login": "تسجيل الدخول",
        "mode_signup": "إنشاء حساب جديد",
        "username": "اسم المستخدم",
        "password": "كلمة المرور",
        "new_username": "اسم مستخدم جديد",
        "new_password": "كلمة مرور جديدة",
        "btn_login": "تسجيل الدخول",
        "btn_signup": "التسجيل",
        "logout": "🔐 تسجيل الخروج",
        "biz_selection": "## 🏢 اختيار نوع العمل",
        "biz_label": "اختر نوع العمل التجاري:",
        "tab1_name": "📊 نموذج الذكاء الاصطناعي الجاهز",
        "tab2_name": "🏋️‍♂️ تدريب النموذج ببيانات CSV الخاصة بك",
        "config_title": "### ⚙️ إعدادات بيانات التنبؤ (النموذج المدمج)",
        "cat_label": "📦 اختر فئة المنتج",
        "branch_label": "🏢 اسم فرع المتجر",
        "price_label": "💵 متوسط سعر المنتج ($)",
        "promo_label": "📢 هل يوجد عرض ترويجي؟",
        "promo_no": "لا يوجد عرض",
        "promo_yes": "يوجد عرض نشط",
        "days_label": "📅 مدة التنبؤ المستقبلية",
        "season_label": "🌤️ التأثير الموسمي",
        "btn_run": "🚀 بدء التنبؤ بالذكاء الاصطناعي",
        "rev_metric": "💰 الإيرادات المتوقعة",
        "stock_metric": "📦 حجم المخزون المطلوب",
        "avg_metric": "📈 متوسط المبيعات اليومية",
        "graph_title": "تنبؤ الذكاء الاصطناعي للفئة",
        "btn_save": "💾 حفظ بيانات التنبؤ",
        "hist_title": "📋 سجل التنبؤات السابقة",
        "hist_info": "ℹ️ لم يتم العثور على سجل تنبؤات سابق لهذا العمل.",
        "success_save": "✅ تم حفظ نتائج التنبؤ بنجاح في السجل!",
        "custom_title": "📁 رفع ملف البيانات الضخمة المخصص",
        "csv_label": "اختر ملف التدريب (ملف CSV):",
        "csv_success": "✅ تم قراءة البيانات بنجاح!",
        "target_label": "🎯 اختر عمود الهدف (Target):",
        "features_label": "⚙️ اختر أعمدة الميزات (Features):",
        "btn_train": "🚀 بدء تدريب نموذج الذكاء الاصطناعي المخصص",
        "train_spinner": "الذكاء الاصطناعي يتعلم من بياناتك الآن...",
        "train_success": "🎉 تم تدريب النموذج المخصص بنجاح!",
        "custom_predict_title": "🔮 إجراء التنبؤات باستخدام النموذج المخصص",
        "custom_mode_label": "🔄 اختر طريقة إدخال البيانات:",
        "mode_manual": "إدخال البيانات يدوياً",
        "mode_csv": "رفع ملف CSV مستقبلي آخر",
        "btn_calc_custom": "حساب التنبؤ المخصص",
        "metric_custom_res": "نتيجة التنبؤ المخصص",
        "btn_predict_file": "🤖 ذكاء اصطناعي: التنبؤ بالملف كاملاً",
        "file_pred_success": "✅ اكتمل التنبؤ بملف CSV بنجاح!",
        "graph_custom_title": "مخطط التنبؤ المخصص لكل صف",
        "custom_hist_title": "📋 سجل التنبؤات المخصصة",
        "custom_hist_info": "ℹ️ لا يوجد سجل تنبؤات مخصص مسبقاً.",
        # Table Columns
        "hist_date": "تاريخ الحفظ", "hist_cat": "الفئة", "hist_branch": "الفرع",
        "hist_price": "السعر ($)", "hist_promo": "العرض الترويجي", "hist_season": "الموسم",
        "hist_days": "المدة", "hist_stock_res": "المخزون المتوقع", "hist_rev_res": "الإيرادات المتوقعة ($)",
        "hist_target": "العمود المستهدف", "hist_features": "الميزات المستخدمة", "hist_pred_val": "نتيجة التنبؤ"
    }
}

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'trained_model' not in st.session_state:
    st.session_state['trained_model'] = None
if 'model_features' not in st.session_state:
    st.session_state['model_features'] = None
if 'tab1_results' not in st.session_state:
    st.session_state['tab1_results'] = None

# --- SIDEBAR LANGUAGE SELECTOR ---
st.sidebar.markdown("## 🌐 LANGUAGE / LUQADDA / اللغة")
lang = st.sidebar.selectbox("Choose Language:", ["English", "Soomaali", "Arabic"])
d = translations[lang]

# --- AUTHENTICATION SCREEN ---
if not st.session_state['logged_in']:
    st.markdown("""
        <style>
        .stApp { background-color: #DDE2E5 !important; }
        div[data-testid="stMainBlockContainer"] { padding-top: 60px !important; max-width: 1000px !important; margin: 0 auto !important; }
        .auth-master-container { display: flex !important; flex-direction: row !important; width: 100% !important; height: 520px !important; background: #FFFFFF !important; border-radius: 20px !important; box-shadow: 0px 15px 35px rgba(0,0,0,0.08) !important; overflow: hidden !important; }
        .spacer-left-panel { background: linear-gradient(135deg, #1E6091 0%, #1A4968 100%) !important; color: white !important; width: 100% !important; height: 180% !important; display: flex !important; flex-direction: column !important; justify-content: center !important; align-items: center !important; text-align: center !important; padding: 40px !important; box-sizing: border-box !important; }
        .spacer-logo { font-size: 50px; background: #FFFFFF; width: 85px; height: 85px; line-height: 85px; border-radius: 50%; margin-bottom: 20px; box-shadow: 0 8px 20px rgba(0,0,0,0.1); color: #1E6091; }
        .spacer-title { font-size: 36px; font-weight: 700; margin-bottom: 12px; color: #FFFFFF !important; }
        .spacer-desc { font-size: 13.5px; opacity: 0.85; max-width: 260px; line-height: 1.6; }
        .main-title-text { color: #1E293B !important; font-size: 26px !important; font-weight: 700 !important; margin-bottom: 4px !important; }
        .sub-title-text { color: #64748B !important; font-size: 14px !important; margin-bottom: 20px !important; }
        .stTextInput > div > div > input { background-color: #F8FAFC !important; border: 1px solid #CBD5E1 !important; border-radius: 8px !important; color: #0F172A !important; padding: 10px 14px !important; font-size: 14px !important; }
        div.stButton > button { border-radius: 8px !important; font-weight: 600 !important; padding: 10px 20px !important; background-color: #1E6091 !important; color: white !important; border: none !important; margin-top: 15px !important; width: 100% !important; height: 44px !important; }
        </style>
    """, unsafe_allow_html=True)

    main_col1, main_col2 = st.columns([2, 3], gap="large")
    
    with main_col1:
        st.markdown(f"""
            <div class="spacer-left-panel" style="border-radius: 40px 0 0 40px; height: 540px;">
                <div class="spacer-logo">🚀</div>
                <div class="spacer-title">Spacer</div>
                <div class="spacer-desc">Welcome to the future of Business Intelligence and automated Sales Forecasting.</div>
            </div>
        """, unsafe_allow_html=True)
        
    with main_col2:
        st.markdown(f'<div class="main-title-text" style="padding-top:20px;">{d["login_title"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sub-title-text">{d["login_desc"]}</div>', unsafe_allow_html=True)
        
        auth_mode = st.radio("Habka:", [d["mode_login"], d["mode_signup"]], horizontal=True, label_visibility="collapsed")
        
        if auth_mode == d["mode_login"]:
            u = st.text_input(d["username"], placeholder="Enter username...", key="user_log_v10")
            p = st.text_input(d["password"], type="password", placeholder="Enter password...", key="pass_log_v10")
            if st.button(d["btn_login"], type="primary", key="btn_signin_v10"):
                if check_user(u, p):
                    st.session_state['logged_in'] = True
                    st.session_state['current_user'] = u
                    st.rerun()
                else: 
                    st.error("❌ Username / Password Error!")
        else:
            nu = st.text_input(d["new_username"], placeholder="Enter new username...", key="user_sign_v10")
            npw = st.text_input(d["new_password"], type="password", placeholder="Enter new password...", key="pass_sign_v10")
            if st.button(d["btn_signup"], type="primary", key="btn_signup_v10"):
                if nu and npw:
                    if add_user(nu, npw):
                        st.success("✅ Account saved! Select 'Login'.")
                    else:
                        st.error("❌ Username already taken!")

# --- MAIN APPLICATION DASHBOARD ---
else:
    st.markdown("""
        <style>
        .stApp { background-color: #0E1117 !important; }
        div[data-testid="stMainBlockContainer"] { max-width: 100% !important; padding-top: 2rem !important; }
        </style>
    """, unsafe_allow_html=True)

    # --- SIDEBAR CONTROLS ---
    st.sidebar.markdown(f"👤 **{d['welcome']}:** {st.session_state['current_user']}")
    if st.sidebar.button(d["logout"]):
        st.session_state['logged_in'] = False
        st.rerun()

    st.sidebar.write("---")
    st.sidebar.markdown(d["biz_selection"])
    
    business_type_raw = st.sidebar.selectbox(
        d["biz_label"],
        ["Supermarket (Suuq Weyn)", "Pharmacy (Farmashiye)", "Clothing Store (Bakhaar Dharka)", "Restaurant (Maqaayad)"]
    )
    business_type = business_type_raw

    if 'last_business_type' not in st.session_state:
        st.session_state['last_business_type'] = business_type
    if st.session_state['last_business_type'] != business_type:
        st.session_state['trained_model'] = None
        st.session_state['model_features'] = None
        st.session_state['tab1_results'] = None
        st.session_state['last_business_type'] = business_type

    categories_dict = {
        "Supermarket (Suuq Weyn)": ["🍎 Groceries & Fresh Produce", "🥛 Dairy & Eggs", "🥩 Meat & Seafood", "🍞 Bakery", "🥤 Beverages"],
        "Pharmacy (Farmashiye)": ["💊 Prescriptions (Daawo)", "🧼 Personal Care", "👶 Baby Products"],
        "Clothing Store (Bakhaar Dharka)": ["👕 Men's Wear", "👗 Women's Fashion", "👟 Shoes & Sneakers"],
        "Restaurant (Maqaayad)": ["🍔 Fast Food", "🍹 Drinks & Desserts", "🍲 Main Dishes"]
    }

    colors_dict = {
        "Supermarket (Suuq Weyn)": {"primary": "#1E3A8A", "accent": "#10B981"},
        "Pharmacy (Farmashiye)": {"primary": "#0891B2", "accent": "#06B6D4"},
        "Clothing Store (Bakhaar Dharka)": {"primary": "#4C1D95", "accent": "#D946EF"},
        "Restaurant (Maqaayad)": {"primary": "#991B1B", "accent": "#F59E0B"}
    }
    current_colors = colors_dict[business_type]

    st.markdown(f"""
        <div style="background-color: {current_colors['primary']}; padding: 20px; border-radius: 10px; text-align: center; color: white; margin-bottom: 25px;">
            <h1>{d['title']}</h1>
            <p style="margin: 5px 0 0 0; opacity: 0.9;">{d['welcome']}: <b>{business_type}</b> | User: <b>{st.session_state['current_user']}</b></p>
        </div>
    """, unsafe_allow_html=True)

    @st.cache_resource
    def train_live_model():
        np.random.seed(42)
        n_samples = 1000
        X = pd.DataFrame({
            'Price': np.random.uniform(1, 100, n_samples),
            'Promo': np.random.choice([0, 1], n_samples),
            'Season': np.random.choice([0, 1, 2], n_samples), 
            'DayOfWeek': np.random.randint(1, 8, n_samples)
        })
        y = 200 + (X['Price'] * -0.5) + (X['Promo'] * 150) + (X['Season'] * 200) - (X['DayOfWeek'] * 10)
        model = RandomForestRegressor(n_estimators=50, random_state=42)
        model.fit(X, y)
        return model

    ai_model = train_live_model()

    tab1, tab2 = st.tabs([d["tab1_name"], d["tab2_name"]])

    # --- TAB 1 ---
    with tab1:
        st.write(d["config_title"])
        col1, col2, col3 = st.columns(3)

        with col1:
            selected_category = st.selectbox(d["cat_label"], categories_dict[business_type], key="cat_tab1")
            store_branch = st.text_input(d["branch_label"], value="Mogadishu Branch", key="branch_tab1")

        with col2:
            item_price = st.number_input(d["price_label"], min_value=1.0, max_value=500.0, value=10.0, key="price_tab1")
            promo = st.radio(d["promo_label"], [d["promo_no"], d["promo_yes"]], horizontal=True, key="promo_tab1")

        with col3:
            forecast_days = st.selectbox(d["days_label"], [7, 15, 30], key="days_tab1")
            season_name = st.selectbox(d["season_label"], ["Maalin Caadi ah", "Ramadaan / Ciid", "Xilli Roobaad"], key="season_tab1")

        season_mapping = {"Maalin Caadi ah": 0, "Ramadaan / Ciid": 1, "Xilli Roobaad": 2}
        promo_val = 1 if promo == d["promo_yes"] else 0

        st.write("---")

        if st.button(f"{d['btn_run']} ({business_type.upper()})", type="primary", use_container_width=True):
            dates = pd.date_range(start=pd.Timestamp.now(), periods=forecast_days)
            future_data = pd.DataFrame({
                'Price': [item_price] * forecast_days,
                'Promo': [promo_val] * forecast_days,
                'Season': [season_mapping[season_name]] * forecast_days,
                'DayOfWeek': dates.dayofweek + 1
            })
            
            predicted_quantities = ai_model.predict(future_data)
            predicted_quantities = np.clip(predicted_quantities, 10, None).astype(int)
            predicted_sales = predicted_quantities * item_price
            
            st.session_state['tab1_results'] = {
                'sales': predicted_sales,
                'quantities': predicted_quantities,
                'dates': dates,
                'category': selected_category,
                'branch': store_branch,
                'price': item_price,
                'promo': promo,
                'season': season_name,
                'days': forecast_days
            }

        if st.session_state['tab1_results'] is not None:
            res = st.session_state['tab1_results']
            m1, m2, m3 = st.columns(3)
            with m1:
                st.markdown(f"<div style='background-color: #065F46; padding: 20px; border-radius: 10px; text-align: center; color: white;'><h4>{d['rev_metric']}</h4><h2>${res['sales'].sum():,.2f}</h2></div>", unsafe_allow_html=True)
            with m2:
                st.markdown(f"<div style='background-color: {current_colors['primary']}; padding: 20px; border-radius: 10px; text-align: center; color: white;'><h4>{d['stock_metric']}</h4><h2>{res['quantities'].sum():,}</h2></div>", unsafe_allow_html=True)
            with m3:
                st.markdown(f"<div style='background-color: #701A75; padding: 20px; border-radius: 10px; text-align: center; color: white;'><h4>{d['avg_metric']}</h4><h2>${res['sales'].mean():,.2f}</h2></div>", unsafe_allow_html=True)
                
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=res['dates'], y=res['sales'], mode='lines+markers', line=dict(color=current_colors['accent'], width=3)))
            fig.update_layout(title=f"{d['graph_title']}: {res['category']}", template="plotly_dark", height=380)
            st.plotly_chart(fig, use_container_width=True)

            if st.button(d["btn_save"], use_container_width=True, key="btn_save_tab1"):
                save_tab1_forecast(
                    st.session_state['current_user'], business_type, res['category'], res['branch'],
                    res['price'], res['promo'], res['season'], res['days'], res['quantities'].sum(), res['sales'].sum()
                )
                st.success(d["success_save"])
                st.rerun()

        st.write("---")
        st.subheader(d["hist_title"])
        
        tab1_hist_df = get_tab1_forecast_history(st.session_state['current_user'], business_type, d)
        
        if not tab1_hist_df.empty:
            st.dataframe(tab1_hist_df, use_container_width=True)
            
            fig_hist_tab1 = go.Figure()
            fig_hist_tab1.add_trace(go.Scatter(
                x=tab1_hist_df[d["hist_date"]], 
                y=tab1_hist_df[d["hist_rev_res"]], 
                mode='lines+markers', 
                line=dict(color=current_colors['accent'], width=2)
            ))
            fig_hist_tab1.update_layout(template="plotly_dark", height=300)
            st.plotly_chart(fig_hist_tab1, use_container_width=True)
        else:
            st.info(d["hist_info"])

    # --- TAB 2 ---
    with tab2:
        st.subheader(d["csv_title"])
        training_file = st.file_uploader(d["csv_label"], type=["csv"], key="trainer_upload")
        
        if training_file is not None:
            train_df = pd.read_csv(training_file)
            st.success(d["csv_success"])
            st.dataframe(train_df.head(5))
            
            all_columns = train_df.columns.tolist()
            target_col = st.selectbox(d["target_label"], all_columns, key="target_tab2")
            remaining_cols = [c for c in all_columns if c != target_col]
            feature_cols = st.multiselect(d["features_label"], remaining_cols, default=remaining_cols[:4] if len(remaining_cols) >= 4 else remaining_cols, key="features_tab2")
            
            if st.button(d["btn_train"], type="primary", use_container_width=True, key="btn_train_tab2"):
                with st.spinner(d["train_spinner"]):
                    X_custom = train_df[feature_cols].fillna(0)
                    y_custom = train_df[target_col].fillna(0)
                    custom_model = RandomForestRegressor(n_estimators=100, random_state=42)
                    custom_model.fit(X_custom, y_custom)
                    
                    st.session_state['trained_model'] = custom_model
                    st.session_state['model_features'] = feature_cols
                    st.session_state['target_column'] = target_col
                    st.session_state['current_business'] = business_type
                    st.balloons()
                    st.success(d["train_success"])

        if st.session_state['trained_model'] is not None:
            st.write("---")
            st.subheader(d["custom_predict_title"])
            input_mode_custom = st.radio(d["custom_mode_label"], [d["mode_manual"], d["mode_csv"]], horizontal=True, key="mode_custom")
            
            if input_mode_custom == d["mode_manual"]:
                user_inputs_custom = {}
                col_slots_custom = st.columns(len(st.session_state['model_features']))
                for idx, feature in enumerate(st.session_state['model_features']):
                    with col_slots_custom[idx]:
                        user_inputs_custom[feature] = st.number_input(f"{feature}:", value=1.0, key=f"input_{feature}")
                
                if st.button(d["btn_calc_custom"], type="primary"):
                    input_df_custom = pd.DataFrame([user_inputs_custom])
                    pred_custom = st.session_state['trained_model'].predict(input_df_custom)[0]
                    st.metric(d["metric_custom_res"], f"{pred_custom:,.2f}")
                    
                    save_custom_forecast(
                        st.session_state['current_user'], business_type, st.session_state['target_column'], 
                        ", ".join(st.session_state['model_features']), pred_custom
                    )
                    st.success("✅ Saved!")
                    st.rerun()
            else:
                test_file_custom = st.file_uploader(d["csv_label"], type=["csv"], key="test_upload_custom")
                if test_file_custom is not None:
                    test_df_custom = pd.read_csv(test_file_custom)
                    if all(col in test_df_custom.columns for col in st.session_state['model_features']):
                        if st.button(d["btn_predict_file"], type="primary", use_container_width=True):
                            X_test_c = test_df_custom[st.session_state['model_features']].fillna(0)
                            preds_c = st.session_state['trained_model'].predict(X_test_c)
                            test_df_custom[f"AI_Predicted_{st.session_state['target_column']}"] = preds_c
                            
                            st.success(d["file_pred_success"])
                            st.dataframe(test_df_custom)
                            
                            fig_c = go.Figure()
                            fig_c.add_trace(go.Bar(x=test_df_custom.index, y=preds_c, marker_color=current_colors['accent']))
                            fig_c.update_layout(title=d["graph_custom_title"], template="plotly_dark", height=380)
                            st.plotly_chart(fig_c, use_container_width=True)
                            
                            save_custom_forecast(
                                st.session_state['current_user'], business_type, st.session_state['target_column'], 
                                f"File: {test_file_custom.name}", preds_c.mean()
                            )

        st.write("---")
        st.subheader(d["custom_hist_title"])
        
        custom_hist_df = get_custom_forecast_history(st.session_state['current_user'], business_type, d)
        
        if not custom_hist_df.empty:
            st.dataframe(custom_hist_df, use_container_width=True)
            
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Scatter(
                x=custom_hist_df[d["hist_date"]], 
                y=custom_hist_df[d["hist_pred_val"]], 
                mode='lines+markers', 
                line=dict(color=current_colors['accent'], width=2)
            ))
            fig_hist.update_layout(template="plotly_dark", height=300)
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info(d["custom_hist_info"])
