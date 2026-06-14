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
    
    # 1. Miiska kaydinta taariikhda ee Tab 1 (Built-in Forecasts)
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

    # 2. Miiska kaydinta taariikhda ee Tab 2 (Custom Forecasts)
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

# --- SHAQOOYINKA KAYDINTA IYO SOO XIGASHADA TAARIIKHDA ---
# Tab 1 Kaydinta
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

# Tab 1 Soo xigashada
def get_tab1_forecast_history(username, b_type):
    conn = sqlite3.connect('users.db')
    df = pd.read_sql_query('''SELECT date_saved AS "Taariikhda", category AS "Qaybta Alaabta", 
                             branch AS "Faraca", price AS "Qiimaha ($)", promo AS "Promotion", 
                             season AS "Xilliga", days AS "Muddada", total_stock AS "Tirada Saadaasha", 
                             total_revenue AS "Dakhliga ($)" 
                             FROM tab1_forecast_history 
                             WHERE username=? AND business_type=? 
                             ORDER BY id DESC''', conn, params=(username, b_type))
    conn.close()
    return df

# Tab 2 Kaydinta
def save_custom_forecast(username, b_type, target, features, value):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''INSERT INTO custom_forecast_history (username, business_type, target_column, features, predicted_value, date_saved)
                 VALUES (?, ?, ?, ?, ?, ?)''', (username, b_type, target, features, float(value), now))
    conn.commit()
    conn.close()

# Tab 2 Soo xigashada
def get_custom_forecast_history(username, b_type):
    conn = sqlite3.connect('users.db')
    df = pd.read_sql_query('''SELECT date_saved AS "Taariikhda", target_column AS "Target-ka", 
                             features AS "Tiirarka (Features)", predicted_value AS "Natiijada Saadaasha" 
                             FROM custom_forecast_history 
                             WHERE username=? AND business_type=? 
                             ORDER BY id DESC''', conn, params=(username, b_type))
    conn.close()
    return df

init_db()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'trained_model' not in st.session_state:
    st.session_state['trained_model'] = None
if 'model_features' not in st.session_state:
    st.session_state['model_features'] = None

# --- QAABEYNTA SEESSINS-KA SAADAASHA TAB 1 ---
if 'tab1_results' not in st.session_state:
    st.session_state['tab1_results'] = None

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
        .spacer-right-panel-container { width: 60% !important; height: 40% !important; padding: 40px 50px !important; box-sizing: border-box !important; background-color: #FFFFFF !important; }
        .main-title-text { color: #1E293B !important; font-size: 30px !important; font-weight: 700 !important; margin-bottom: 4px !important; }
        .sub-title-text { color: #64748B !important; font-size: 14px !important; margin-bottom: 20px !important; }
        .stTextInput > div > div > input { background-color: #F8FAFC !important; border: 1px solid #CBD5E1 !important; border-radius: 8px !important; color: #0F172A !important; padding: 10px 14px !important; font-size: 14px !important; }
        .stTextInput label p { font-size: 16px !important; color: #475569 !important; font-weight: 600 !important; margin-bottom: 4px !important; }
        div.stButton > button { border-radius: 8px !important; font-weight: 600 !important; padding: 10px 20px !important; background-color: #1E6091 !important; color: white !important; border: none !important; margin-top: 15px !important; width: 100% !important; height: 44px !important; transition: all 0.3s ease; }
        div.stButton > button:hover { background-color: #1A4968 !important; box-shadow: 0 4px 12px rgba(30, 96, 145, 0.3) !important; }
        div[data-testid="stRadio"] label p { font-size: 14px !important; color: #475569 !important; }
        </style>
    """, unsafe_allow_html=True)

    main_col1, main_col2 = st.columns([2, 3], gap="large")
    
    with main_col1:
        st.markdown("""
            <div class="spacer-left-panel" style="border-radius: 40px 0 0 40px; height: 540px;">
                <div class="spacer-logo">🚀</div>
                <div class="spacer-title">Spacer</div>
                <div class="spacer-desc">Welcome to the future of Business Intelligence and automated Sales Forecasting.</div>
            </div>
        """, unsafe_allow_html=True)
        
    with main_col2:
        st.markdown('<div class="main-title-text" style="padding-top:20px;">Create your account</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-title-text">Fadlan dooro habka aad rabto inaad u gasho nidaamka.</div>', unsafe_allow_html=True)
        
        auth_mode = st.radio("Habka:", ["Soo Gal (Login)", "Is-diwaangeli (Sign Up)"], horizontal=True, label_visibility="collapsed")
        
        if auth_mode == "Soo Gal (Login)":
            u = st.text_input("Username (Magacaaga)", placeholder="Enter your username...", key="user_log_v9")
            p = st.text_input("Password (Sirtaada)", type="password", placeholder="Enter your password...", key="pass_log_v9")
            if st.button("Sign In", type="primary", key="btn_signin_v9"):
                if check_user(u, p):
                    st.session_state['logged_in'] = True
                    st.session_state['current_user'] = u
                    st.rerun()
                else: 
                    st.error("❌ Username ama Password baa khaldan!")
        else:
            nu = st.text_input("New Username (Magac Cusub)", placeholder="Enter your new username...", key="user_sign_v9")
            npw = st.text_input("New Password (Sir Cusub)", type="password", placeholder="Enter your new password...", key="pass_sign_v9")
            if st.button("Sign Up", type="primary", key="btn_signup_v9"):
                if nu and npw:
                    if add_user(nu, npw):
                        st.success("✅ Account-ka waa la keydiyey! Hada dooro 'Soo Gal'.")
                    else:
                        st.error("❌ Magacan mar hore ayaa la qaatay!")
                else:
                    st.warning("⚠️ Fadlan buuxi meelaha banaan.")

# --- MAIN APPLICATION DASHBOARD ---
else:
    st.markdown("""
        <style>
        .stApp { background-color: #0E1117 !important; }
        div[data-testid="stMainBlockContainer"] { max-width: 100% !important; padding-top: 2rem !important; }
        </style>
    """, unsafe_allow_html=True)

    # --- SIDEBAR CONTROLS ---
    st.sidebar.markdown(f"👤 **User:** {st.session_state['current_user']}")
    if st.sidebar.button("🔐 Log Out (Ka Bax)"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.sidebar.write("---")
    st.sidebar.markdown("## 🏢 DOORASHADA GANACSIGA")
    business_type = st.sidebar.selectbox(
        "Dooro nooca ganacosiga aad rabto:",
        ["Supermarket (Suuq Weyn)", "Pharmacy (Farmashiye)", "Clothing Store (Bakhaar Dharka)", "Restaurant (Maqaayad)"]
    )

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
            <h1>🤖 UNIVERSAL BUSINESS AI FORECASTER</h1>
            <p style="margin: 5px 0 0 0; opacity: 0.9;">Hadda waxaad maamulaysaa: <b>{business_type}</b> | User: <b>{st.session_state['current_user']}</b></p>
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

    tab1, tab2 = st.tabs(["📊 MODEL-KII HORE EE DIYAARKA AH", "🏋️‍♂️ U TABABAR AI-GA XOGTAADA CSV"])

    # --- TAB 1 ---
    with tab1:
        st.write("### ⚙️ QAABAYNTA XOGTA SAADAASHA (BUILT-IN AI MODEL)")
        col1, col2, col3 = st.columns(3)

        with col1:
            selected_category = st.selectbox("📦 Dooro Qaybta Alaabta (Category)", categories_dict[business_type], key="cat_tab1")
            store_branch = st.text_input("🏢 Magaca Faraca/Dukaanka", value="Mogadishu Branch", key="branch_tab1")

        with col2:
            item_price = st.number_input("💵 Celceliska Qiimaha Alaabta ($)", min_value=1.0, max_value=500.0, value=10.0, key="price_tab1")
            promo = st.radio("📢 Qiimo Dhimis Ma Jiraa (Promotion)?", ["Maya (No Promo)", "Haa (Active Promo)"], horizontal=True, key="promo_tab1")

        with col3:
            forecast_days = st.selectbox("📅 Muddada Saadaasha", [7, 15, 30], key="days_tab1")
            season_name = st.selectbox("🌤️ Saamaynta Xilliga", ["Maalin Caadi ah", "Ramadaan / Ciid", "Xilli Roobaad"], key="season_tab1")

        season_mapping = {"Maalin Caadi ah": 0, "Ramadaan / Ciid": 1, "Xilli Roobaad": 2}
        promo_val = 1 if promo == "Haa (Active Promo)" else 0

        st.write("---")

        if st.button(f"🚀 BILAABO SAADAASHA {business_type.upper()}", type="primary", use_container_width=True):
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
            
            # Kaydi natiijada xilligan la xisaabiyay si badhanka Save u isticmaalo
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

        # Haddii ay xog diyaar tahay, muuji Metrics-ka iyo Garaafka
        if st.session_state['tab1_results'] is not None:
            res = st.session_state['tab1_results']
            m1, m2, m3 = st.columns(3)
            with m1:
                st.markdown(f"<div style='background-color: #065F46; padding: 20px; border-radius: 10px; text-align: center; color: white;'><h4>💰 REVENUE (AI Prediction)</h4><h2>${res['sales'].sum():,.2f}</h2></div>", unsafe_allow_html=True)
            with m2:
                st.markdown(f"<div style='background-color: {current_colors['primary']}; padding: 20px; border-radius: 10px; text-align: center; color: white;'><h4>📦 STOCK DEMAND</h4><h2>{res['quantities'].sum():,} Xabo</h2></div>", unsafe_allow_html=True)
            with m3:
                st.markdown(f"<div style='background-color: #701A75; padding: 20px; border-radius: 10px; text-align: center; color: white;'><h4>📈 AVG DAILY SALES</h4><h2>${res['sales'].mean():,.2f}</h2></div>", unsafe_allow_html=True)
                
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=res['dates'], y=res['sales'], mode='lines+markers', line=dict(color=current_colors['accent'], width=3)))
            fig.update_layout(title=f"Saadaasha AI ee Qaybta: {res['category']}", template="plotly_dark", height=380)
            st.plotly_chart(fig, use_container_width=True)

            # Badhanka Kaydinta Xogta Tab 1
            if st.button("💾 SAVE FORECAST DATA (KAYDI)", use_container_width=True, key="btn_save_tab1"):
                save_tab1_forecast(
                    st.session_state['current_user'],
                    business_type,
                    res['category'],
                    res['branch'],
                    res['price'],
                    res['promo'],
                    res['season'],
                    res['days'],
                    res['quantities'].sum(),
                    res['sales'].sum()
                )
                st.success("✅ Natiijadii saadaasha Tab 1 si guul leh ayaa loo kaydiyey taariikhda!")
                st.rerun()

        # --- QAYBTA TAARIIKHDA IYO GARAAFKA TAARIIKHDA CUSUB EE TAB 1 ---
        st.write("---")
        st.subheader(f"📋 TAARIIKHDA SAADAASHII HORE EE {business_type.upper()}")
        
        tab1_hist_df = get_tab1_forecast_history(st.session_state['current_user'], business_type)
        
        if not tab1_hist_df.empty:
            st.dataframe(tab1_hist_df, use_container_width=True)
            
            # Garaafka Isbeddelka Taariikhda Tab 1
            fig_hist_tab1 = go.Figure()
            fig_hist_tab1.add_trace(go.Scatter(
                x=tab1_hist_df["Taariikhda"], 
                y=tab1_hist_df["Dakhliga ($)"], 
                mode='lines+markers', 
                line=dict(color=current_colors['accent'], width=2)
            ))
            fig_hist_tab1.update_layout(
                title="Isbeddelka Dakhliga Saadaalihii Hore ee aad Kaydisay", 
                xaxis_title="Taariikhda Kaydka", 
                yaxis_title="Waqtiga / Celceliska Dakhliga ($)",
                template="plotly_dark", 
                height=300
            )
            st.plotly_chart(fig_hist_tab1, use_container_width=True)
        else:
            st.info(f"ℹ️ Weligaa wax saadaal ah ma aad kaydsan oo ku saabsan ganacsiga {business_type}.")

    # --- TAB 2 ---
    with tab2:
        st.subheader(f"📁 Soo Geli Xogta weyn ee Custom-ka ah ee {business_type}")
        training_file = st.file_uploader("Dooro Faylka Tababarka (CSV File):", type=["csv"], key="trainer_upload")
        
        if training_file is not None:
            train_df = pd.read_csv(training_file)
            st.success("✅ Xogtii si guul leh ayaa loo soo akhriyey!")
            st.dataframe(train_df.head(5))
            
            all_columns = train_df.columns.tolist()
            target_col = st.selectbox("🎯 Dooro tiirka ah Target-ka:", all_columns, key="target_tab2")
            remaining_cols = [c for c in all_columns if c != target_col]
            feature_cols = st.multiselect("⚙️ Dooro tiirarka (Features):", remaining_cols, default=remaining_cols[:4] if len(remaining_cols) >= 4 else remaining_cols, key="features_tab2")
            
            if st.button("🚀 BILOW TABABARKA MODEL-KA CUSTOM-KA AH", type="primary", use_container_width=True, key="btn_train_tab2"):
                with st.spinner("AI-ga ayaa hadda baranaya..."):
                    X_custom = train_df[feature_cols].fillna(0)
                    y_custom = train_df[target_col].fillna(0)
                    custom_model = RandomForestRegressor(n_estimators=100, random_state=42)
                    custom_model.fit(X_custom, y_custom)
                    
                    st.session_state['trained_model'] = custom_model
                    st.session_state['model_features'] = feature_cols
                    st.session_state['target_column'] = target_col
                    st.session_state['current_business'] = business_type
                    st.balloons()
                    st.success("🎉 AI Custom Model-kii guul ayuu ku bartay xogtaada!")

        if st.session_state['trained_model'] is not None:
            st.write("---")
            st.subheader("🔮 Ku Samee Saadaal Model-kaagii Custom-ka ahaa")
            input_mode_custom = st.radio("🔄 Dooro qaabka xogta:", ["Gacanta ku geli xog yar", "Fayl CSV kale oo mustaqbalka ah soo geli"], horizontal=True, key="mode_custom")
            
            if input_mode_custom == "Gacanta ku geli xog yar":
                user_inputs_custom = {}
                col_slots_custom = st.columns(len(st.session_state['model_features']))
                for idx, feature in enumerate(st.session_state['model_features']):
                    with col_slots_custom[idx]:
                        user_inputs_custom[feature] = st.number_input(f"{feature}:", value=1.0, key=f"input_{feature}")
                
                if st.button("XISSAABI SAADAASHA CUSTOM-KA AH", type="primary"):
                    input_df_custom = pd.DataFrame([user_inputs_custom])
                    pred_custom = st.session_state['trained_model'].predict(input_df_custom)[0]
                    st.metric("Natiijada Saadaasha Custom-ka ah", f"{pred_custom:,.2f}")
                    
                    save_custom_forecast(
                        st.session_state['current_user'], 
                        business_type, 
                        st.session_state['target_column'], 
                        ", ".join(st.session_state['model_features']), 
                        pred_custom
                    )
                    st.success("✅ Natiijadii saadaasha custom-ka ah waa la kaydiyey!")
                    st.rerun()
            else:
                test_file_custom = st.file_uploader("Dooro faylka mustaqbalka ee CSV-ga ah:", type=["csv"], key="test_upload_custom")
                if test_file_custom is not None:
                    test_df_custom = pd.read_csv(test_file_custom)
                    if all(col in test_df_custom.columns for col in st.session_state['model_features']):
                        if st.button("🤖 AI: SAADAALI FAYLKAN OO DHAN", type="primary", use_container_width=True):
                            X_test_c = test_df_custom[st.session_state['model_features']].fillna(0)
                            preds_c = st.session_state['trained_model'].predict(X_test_c)
                            test_df_custom[f"AI_Predicted_{st.session_state['target_column']}"] = preds_c
                            
                            st.success("✅ Saadaashii falka CSV waa dhammaystirmay!")
                            st.dataframe(test_df_custom)
                            
                            fig_c = go.Figure()
                            fig_c.add_trace(go.Bar(
                                x=test_df_custom.index, 
                                y=preds_c, 
                                name='Saadaasha Custom', 
                                marker_color=current_colors['accent']
                            ))
                            fig_c.update_layout(title=f"Garaafka Saadaasha Cusub ee Row kasta ({st.session_state['target_column']})", template="plotly_dark", height=380)
                            st.plotly_chart(fig_c, use_container_width=True)
                            
                            save_custom_forecast(
                                st.session_state['current_user'], 
                                business_type, 
                                st.session_state['target_column'], 
                                f"Faylka: {test_file_custom.name}", 
                                preds_c.mean()
                            )

        st.write("---")
        st.subheader(f"📋 TAARIIKHDA SAADAASHII CUSTOM-KA AH ({business_type.upper()})")
        
        custom_hist_df = get_custom_forecast_history(st.session_state['current_user'], business_type)
        
        if not custom_hist_df.empty:
            st.dataframe(custom_hist_df, use_container_width=True)
            
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Scatter(
                x=custom_hist_df["Taariikhda"], 
                y=custom_hist_df["Natiijada Saadaasha"], 
                mode='lines+markers', 
                line=dict(color=current_colors['accent'], width=2)
            ))
            fig_hist.update_layout(title="Isbeddelka Natiijooyinkii Saadaasha ee Hore loo Kaydiyey", xaxis_title="Taariikhda Kaydka", yaxis_title="Qiimaha la Saadaaliyey", template="plotly_dark", height=300)
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info(f"ℹ️ Ma jirto taariikh saadaal custom ah oo hore loogu sameeyay ganacsiga {business_type}.")