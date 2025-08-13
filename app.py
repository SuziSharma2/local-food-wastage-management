import os
import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime, date, timedelta

import plotly.express as px  # charts

from scripts.create_tables import create_tables
from scripts.queries import SQL_QUERIES

DB_PATH = "db/food_wastage.db"

# ------------- Utilities -------------
def get_conn():
    os.makedirs("db", exist_ok=True)
    create_tables(DB_PATH)
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def read_sql(query, params=None):
    conn = get_conn()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def exec_sql(query, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params or [])
    conn.commit()
    conn.close()

@st.cache_data
def cached_read(query, params_tuple=None, _ts=None):
    return read_sql(query, params_tuple)

def cache_bust():
    st.session_state["ts"] = datetime.now().isoformat()

def ts():
    return st.session_state.get("ts", "0")

# ------------- Page -------------
st.set_page_config(page_title="Local Food Wastage Management", layout="wide")
st.title("🍲 Local Food Wastage Management System")

with st.sidebar:
    st.header("⚙️ Admin / Data")
    st.caption("Upload CSVs to (re)load the database.")
    prov_file = st.file_uploader("providers_data.csv", type=["csv"], key="prov")
    recv_file = st.file_uploader("receivers_data.csv", type=["csv"], key="recv")
    food_file = st.file_uploader("food_listings_data.csv", type=["csv"], key="food")
    claim_file = st.file_uploader("claims_data.csv", type=["csv"], key="claim")

    if st.button("📥 Load Uploaded CSVs"):
        conn = get_conn()
        if prov_file: pd.read_csv(prov_file).to_sql("providers", conn, if_exists="replace", index=False)
        if recv_file: pd.read_csv(recv_file).to_sql("receivers", conn, if_exists="replace", index=False)
        if food_file: pd.read_csv(food_file).to_sql("food_listings", conn, if_exists="replace", index=False)
        if claim_file: pd.read_csv(claim_file).to_sql("claims", conn, if_exists="replace", index=False)
        conn.close()
        cache_bust()
        st.success("CSV(s) loaded and DB updated.")

    st.divider()
    st.header("🔎 Dashboard Filter")
    city_filter = st.text_input("City for provider contacts", value="")

tabs = st.tabs(["📊 Dashboard", "🏪 Providers", "👥 Receivers", "🍱 Food Listings", "📦 Claims"])

# ===== Helper: live table readers (no cache for CRUD tables) =====
def table_df(table_name):
    return read_sql(f"SELECT * FROM {table_name}")

# ===== Derived queries for charts =====
def df_provider_types():
    return read_sql("SELECT Type, COUNT(*) AS contributions FROM providers GROUP BY Type ORDER BY contributions DESC")

def df_food_types():
    return read_sql("SELECT Food_Type, COUNT(*) AS count FROM food_listings GROUP BY Food_Type ORDER BY count DESC")

def df_claim_status_pct():
    return read_sql("""
        SELECT Status, ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM claims), 2) AS percentage
        FROM claims GROUP BY Status
    """)

def df_city_listings():
    return read_sql("""
        SELECT Location AS City, COUNT(*) AS listings
        FROM food_listings
        GROUP BY Location
        ORDER BY listings DESC
        LIMIT 10
    """)

def df_completed_claims_over_time():
    # Daily completed claims trend
    return read_sql("""
        SELECT date(Timestamp) AS day, COUNT(*) AS completed
        FROM claims
        WHERE Status='Completed' AND Timestamp IS NOT NULL
        GROUP BY date(Timestamp)
        ORDER BY day
    """)

# ---------- Dashboard ----------
with tabs[0]:
    st.subheader("📈 Visual Insights")

    colA, colB = st.columns(2)
    with colA:
        df_pt = df_provider_types()
        if not df_pt.empty:
            fig = px.bar(df_pt, x="Type", y="contributions", title="Top Provider Types (Count)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No provider data available for chart.")

    with colB:
        df_cs = df_claim_status_pct()
        if not df_cs.empty:
            fig = px.pie(df_cs, names="Status", values="percentage", title="Claim Status (%)", hole=0.35)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No claims data available for chart.")

    colC, colD = st.columns(2)
    with colC:
        df_ft = df_food_types()
        if not df_ft.empty:
            fig = px.bar(df_ft, x="Food_Type", y="count", title="Most Common Food Types")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No food listings for chart.")

    with colD:
        df_trend = df_completed_claims_over_time()
        if not df_trend.empty:
            fig = px.line(df_trend, x="day", y="completed", title="Completed Claims Over Time")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No completed claims trend available.")

    st.divider()
    st.subheader("🧮 SQL Query Outputs")

    for name, query in SQL_QUERIES.items():
        st.markdown(f"**{name}**")
        if "WHERE City = ?" in query:
            if city_filter.strip():
                df = cached_read(query, (city_filter.strip(),), ts())
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Enter a city in the sidebar to run this query.")
        else:
            df = cached_read(query, None, ts())
            st.dataframe(df, use_container_width=True)
        st.divider()

# ---------- Providers CRUD ----------
with tabs[1]:
    st.subheader("🏪 Providers (CRUD)")
    # Search bar
    search = st.text_input("Search providers by name/city/type", key="ps")
    base_df = table_df("providers")
    if search:
        s = search.lower()
        mask = (
            base_df["Name"].astype(str).str.lower().str.contains(s) |
            base_df["City"].astype(str).str.lower().str.contains(s) |
            base_df["Type"].astype(str).str.lower().str.contains(s)
        )
        view_df = base_df[mask]
    else:
        view_df = base_df

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Create / Update Provider**")
        p_id = st.number_input("Provider_ID (0 to auto)", min_value=0, step=1)
        p_name = st.text_input("Name*")
        p_type = st.text_input("Type (Restaurant, Grocery Store, ...)")
        p_addr = st.text_input("Address")
        p_city = st.text_input("City")
        p_contact = st.text_input("Contact")
        if st.button("💾 Save Provider"):
            if not p_name:
                st.error("Name is required.")
            else:
                if p_id == 0:
                    exec_sql("INSERT INTO providers(Name, Type, Address, City, Contact) VALUES (?,?,?,?,?)",
                             (p_name, p_type, p_addr, p_city, p_contact))
                else:
                    exec_sql(
                        """INSERT INTO providers(Provider_ID, Name, Type, Address, City, Contact)
                           VALUES (?,?,?,?,?,?)
                           ON CONFLICT(Provider_ID) DO UPDATE SET
                               Name=excluded.Name, Type=excluded.Type, Address=excluded.Address,
                               City=excluded.City, Contact=excluded.Contact""",
                        (p_id, p_name, p_type, p_addr, p_city, p_contact)
                    )
                cache_bust()
                st.success("Provider saved.")
    with col2:
        del_id = st.number_input("Provider_ID to delete", min_value=0, step=1, key="delp")
        if st.button("🗑️ Delete Provider"):
            if del_id > 0:
                exec_sql("DELETE FROM providers WHERE Provider_ID = ?", (del_id,))
                cache_bust()
                st.success(f"Provider {del_id} deleted.")
            else:
                st.error("Enter a valid Provider_ID.")

    st.markdown("**Providers**")
    st.dataframe(view_df.sort_values("Provider_ID"), use_container_width=True)

# ---------- Receivers CRUD ----------
with tabs[2]:
    st.subheader("👥 Receivers (CRUD)")
    search = st.text_input("Search receivers by name/city/type", key="rs")
    base_df = table_df("receivers")
    if search:
        s = search.lower()
        mask = (
            base_df["Name"].astype(str).str.lower().str.contains(s) |
            base_df["City"].astype(str).str.lower().str.contains(s) |
            base_df["Type"].astype(str).str.lower().str.contains(s)
        )
        view_df = base_df[mask]
    else:
        view_df = base_df

    col1, col2 = st.columns(2)
    with col1:
        r_id = st.number_input("Receiver_ID (0 to auto)", min_value=0, step=1)
        r_name = st.text_input("Name*", key="rname")
        r_type = st.text_input("Type (NGO, Individual, ...)")
        r_city = st.text_input("City", key="rcity")
        r_contact = st.text_input("Contact", key="rcontact")
        if st.button("💾 Save Receiver"):
            if not r_name:
                st.error("Name is required.")
            else:
                if r_id == 0:
                    exec_sql("INSERT INTO receivers(Name, Type, City, Contact) VALUES (?,?,?,?)",
                             (r_name, r_type, r_city, r_contact))
                else:
                    exec_sql(
                        """INSERT INTO receivers(Receiver_ID, Name, Type, City, Contact)
                           VALUES (?,?,?,?,?)
                           ON CONFLICT(Receiver_ID) DO UPDATE SET
                               Name=excluded.Name, Type=excluded.Type, City=excluded.City, Contact=excluded.Contact""",
                        (r_id, r_name, r_type, r_city, r_contact))
                cache_bust()
                st.success("Receiver saved.")
    with col2:
        del_rid = st.number_input("Receiver_ID to delete", min_value=0, step=1, key="delr")
        if st.button("🗑️ Delete Receiver"):
            if del_rid > 0:
                exec_sql("DELETE FROM receivers WHERE Receiver_ID = ?", (del_rid,))
                cache_bust()
                st.success(f"Receiver {del_rid} deleted.")
            else:
                st.error("Enter a valid Receiver_ID.")

    st.markdown("**Receivers**")
    st.dataframe(view_df.sort_values("Receiver_ID"), use_container_width=True)

# ---------- Food Listings CRUD + Expiry Alerts ----------
with tabs[3]:
    st.subheader("🍱 Food Listings (CRUD)")
    search = st.text_input("Search food by name/city/type/meal", key="fs")
    base_df = table_df("food_listings")

    # Expiry calculations
    if not base_df.empty:
        base_df["Expiry_Date"] = pd.to_datetime(base_df["Expiry_Date"], errors="coerce")
        today = pd.Timestamp(date.today())
        base_df["Days_To_Expiry"] = (base_df["Expiry_Date"] - today).dt.days
    else:
        base_df["Days_To_Expiry"] = []

    if search:
        s = search.lower()
        mask = (
            base_df["Food_Name"].astype(str).str.lower().str.contains(s) |
            base_df["Location"].astype(str).str.lower().str.contains(s) |
            base_df["Food_Type"].astype(str).str.lower().str.contains(s) |
            base_df["Meal_Type"].astype(str).str.lower().str.contains(s)
        )
        view_df = base_df[mask]
    else:
        view_df = base_df

    # Alerts section
    st.markdown("**⏰ Expiry Alerts (≤ 3 days)**")
    alert_df = base_df[(base_df["Days_To_Expiry"].notna()) & (base_df["Days_To_Expiry"] <= 3)]
    if alert_df.empty:
        st.success("No items expiring in the next 3 days.")
    else:
        st.warning("Items expiring soon:")
        st.dataframe(alert_df.sort_values("Days_To_Expiry"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        f_id = st.number_input("Food_ID (0 to auto)", min_value=0, step=1)
        f_name = st.text_input("Food_Name*", key="fname")
        f_qty = st.number_input("Quantity", min_value=0, step=1, key="fqty")
        f_exp = st.date_input("Expiry_Date", value=date.today() + timedelta(days=1))
        f_pid = st.number_input("Provider_ID (must exist in providers)", min_value=0, step=1)
        f_ptype = st.text_input("Provider_Type")
        f_loc = st.text_input("Location (City)")
        f_ftype = st.text_input("Food_Type (Veg/Non-Veg/Vegan...)")
        f_meal = st.text_input("Meal_Type (Breakfast/Lunch/Dinner/Snacks)")
        if st.button("💾 Save Food Listing"):
            if not f_name:
                st.error("Food_Name is required.")
            else:
                if f_id == 0:
                    exec_sql(
                        """INSERT INTO food_listings
                           (Food_Name, Quantity, Expiry_Date, Provider_ID, Provider_Type, Location, Food_Type, Meal_Type)
                           VALUES (?,?,?,?,?,?,?,?)""",
                        (f_name, int(f_qty), f_exp.isoformat(), f_pid if f_pid > 0 else None,
                         f_ptype, f_loc, f_ftype, f_meal),
                    )
                else:
                    exec_sql(
                        """INSERT INTO food_listings
                           (Food_ID, Food_Name, Quantity, Expiry_Date, Provider_ID, Provider_Type, Location, Food_Type, Meal_Type)
                           VALUES (?,?,?,?,?,?,?,?,?)
                           ON CONFLICT(Food_ID) DO UPDATE SET
                             Food_Name=excluded.Food_Name,
                             Quantity=excluded.Quantity,
                             Expiry_Date=excluded.Expiry_Date,
                             Provider_ID=excluded.Provider_ID,
                             Provider_Type=excluded.Provider_Type,
                             Location=excluded.Location,
                             Food_Type=excluded.Food_Type,
                             Meal_Type=excluded.Meal_Type""",
                        (f_id, f_name, int(f_qty), f_exp.isoformat(), f_pid if f_pid > 0 else None,
                         f_ptype, f_loc, f_ftype, f_meal),
                    )
                cache_bust()
                st.success("Food listing saved.")
    with col2:
        del_fid = st.number_input("Food_ID to delete", min_value=0, step=1, key="delf")
        if st.button("🗑️ Delete Food Listing"):
            if del_fid > 0:
                exec_sql("DELETE FROM food_listings WHERE Food_ID = ?", (del_fid,))
                cache_bust()
                st.success(f"Food listing {del_fid} deleted.")
            else:
                st.error("Enter a valid Food_ID.")

    st.markdown("**Food Listings**")
    st.dataframe(view_df.sort_values("Food_ID"), use_container_width=True)

# ---------- Claims CRUD ----------
with tabs[4]:
    st.subheader("📦 Claims (CRUD)")
    search = st.text_input("Search claims by status / timestamp / IDs", key="cs")
    base_df = table_df("claims")
    if search:
        s = search.lower()
        mask = (
            base_df["Status"].astype(str).str.lower().str.contains(s) |
            base_df["Timestamp"].astype(str).str.lower().str.contains(s) |
            base_df["Claim_ID"].astype(str).str.contains(s) |
            base_df["Food_ID"].astype(str).str.contains(s) |
            base_df["Receiver_ID"].astype(str).str.contains(s)
        )
        view_df = base_df[mask]
    else:
        view_df = base_df

    col1, col2 = st.columns(2)
    with col1:
        c_id = st.number_input("Claim_ID (0 to auto)", min_value=0, step=1)
        c_food = st.number_input("Food_ID (must exist)", min_value=0, step=1)
        c_recv = st.number_input("Receiver_ID (must exist)", min_value=0, step=1)
        c_status = st.selectbox("Status", ["Pending", "Completed", "Cancelled"])
        c_ts = st.text_input("Timestamp (auto if blank, ISO 8601)", value="")
        if st.button("💾 Save Claim"):
            ts_val = c_ts.strip() or datetime.now().isoformat(timespec="seconds")
            if c_id == 0:
                exec_sql(
                    "INSERT INTO claims(Food_ID, Receiver_ID, Status, Timestamp) VALUES (?,?,?,?)",
                    (c_food if c_food > 0 else None, c_recv if c_recv > 0 else None, c_status, ts_val)
                )
            else:
                exec_sql(
                    """INSERT INTO claims(Claim_ID, Food_ID, Receiver_ID, Status, Timestamp)
                       VALUES (?,?,?,?,?)
                       ON CONFLICT(Claim_ID) DO UPDATE SET
                         Food_ID=excluded.Food_ID,
                         Receiver_ID=excluded.Receiver_ID,
                         Status=excluded.Status,
                         Timestamp=excluded.Timestamp""",
                    (c_id, c_food if c_food > 0 else None, c_recv if c_recv > 0 else None, c_status, ts_val)
                )
            cache_bust()
            st.success("Claim saved.")
    with col2:
        del_cid = st.number_input("Claim_ID to delete", min_value=0, step=1, key="delc")
        if st.button("🗑️ Delete Claim"):
            if del_cid > 0:
                exec_sql("DELETE FROM claims WHERE Claim_ID = ?", (del_cid,))
                cache_bust()
                st.success(f"Claim {del_cid} deleted.")
            else:
                st.error("Enter a valid Claim_ID.")

    st.markdown("**Claims**")
    st.dataframe(view_df.sort_values("Claim_ID"), use_container_width=True)
