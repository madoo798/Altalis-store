import streamlit as st
from streamlit_option_menu import option_menu
import libsql
import pandas as pd
import os

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Altalis & Celesta Admin Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Metallic / Dark Theme
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #c9d1d9;
    }
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# TURSO CLOUD DATABASE CONNECTION & SETUP
# ==========================================
TURSO_URL = os.getenv("TURSO_DATABASE_URL", "libsql://altalis-store-madoki.aws-eu-west-1.turso.io")
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODU1MjEzNjYsImlkIjoiMDE5ZmI5NWMtYTcwMS03NzY2LWFiYWMtMzlkZjJhMzBkYzgyIiwia2lkIjoieG53aGlueTM1VS1NMnlUeTNZTmJ5LTI0dS1MbXdsbjNNeEZ1cWFoSmhPMCIsInJpZCI6ImJhZjJkYTc0LTNkYjctNDIzMy05MTVhLWMxZmMwZWZhNjA3NiJ9.2o12r3dqEQ7jmWOc7RyILcXQLzuInsZJDXegUh6IR7q6xGwpi7LmySgcBYYXh4W2t2iIOQBIxJZmID6UNqvGBw")

def get_turso_connection():
    """Create a secure connection to the Turso cloud database."""
    if TURSO_URL.startswith("libsql://") or TURSO_URL.startswith("https://"):
        return libsql.connect(TURSO_URL, auth_token=TURSO_TOKEN)
    else:
        return libsql.connect(TURSO_URL)

def init_cloud_db():
    """Automatically create database tables in Turso if they don't exist."""
    try:
        conn = get_turso_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance_usd REAL DEFAULT 0.0,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price_usd REAL NOT NULL,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                is_sold BOOLEAN DEFAULT 0,
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                invoice_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                amount_usd REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                delivered_content TEXT NOT NULL,
                purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Init DB Error: {e}")

# Initialize tables on startup
init_cloud_db()

def get_data(query: str) -> pd.DataFrame:
    """Fetch query results from Turso cloud database as a Pandas DataFrame."""
    try:
        conn = get_turso_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if not rows:
            conn.close()
            return pd.DataFrame()
            
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        return pd.DataFrame(rows, columns=columns)
    except Exception as e:
        st.error(f"Database query error: {e}")
        return pd.DataFrame()

def execute_query(query: str, params: tuple = ()):
    """Execute write/update/insert queries safely on Turso cloud."""
    try:
        conn = get_turso_connection()
        conn.execute(query, params)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Database execution error: {e}")
        return False

def get_single_value(query: str) -> float:
    """Fetch a single numeric aggregate value from Turso cloud."""
    try:
        conn = get_turso_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        row = cursor.fetchone()
        conn.close()
        return row[0] if row and row[0] is not None else 0.0
    except Exception:
        return 0.0

# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/server.png", width=100)
    st.title("Altalis & Celesta")
    st.caption("Cloud Admin Dashboard (Turso)")
    
    selected = option_menu(
        menu_title="Store Management",
        options=["Overview", "Products & Stock", "Orders", "Users & Balances", "Invoices"],
        icons=["speedometer2", "box-seam", "receipt", "people", "wallet2"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#161b22"},
            "icon": {"color": "#58a6ff", "font-size": "18px"},
            "nav-link": {"font-size": "14px", "text-align": "left", "margin": "0px", "--hover-color": "#30363d"},
            "nav-link-selected": {"background-color": "#238636"},
        }
    )

# ==========================================
# 1. OVERVIEW PAGE
# ==========================================
if selected == "Overview":
    st.title("⚡ Store Performance Overview")
    st.markdown("Real-time telemetry synced securely via your **Turso Cloud Database**.")
    st.markdown("---")

    # Fetch Metrics
    total_users = get_single_value("SELECT COUNT(*) FROM users")
    total_revenue = get_single_value("SELECT SUM(amount_usd) FROM invoices WHERE status = 'paid'")
    total_orders = get_single_value("SELECT COUNT(*) FROM orders")
    active_products = get_single_value("SELECT COUNT(*) FROM products WHERE is_active = 1")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Users", f"{int(total_users)}")
    with col2:
        st.metric("Total Revenue", f"${total_revenue:.2f}")
    with col3:
        st.metric("Completed Orders", f"{int(total_orders)}")
    with col4:
        st.metric("Active Products", f"{int(active_products)}")

    st.markdown("---")
    
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Recent Orders")
        orders_df = get_data("SELECT * FROM orders ORDER BY purchased_at DESC LIMIT 5")
        if not orders_df.empty:
            st.dataframe(orders_df, use_container_width=True)
        else:
            st.info("No orders recorded yet.")

    with col_right:
        st.subheader("Recent Paid Invoices")
        invoices_df = get_data("SELECT * FROM invoices WHERE status = 'paid' ORDER BY created_at DESC LIMIT 5")
        if not invoices_df.empty:
            st.dataframe(invoices_df, use_container_width=True)
        else:
            st.info("No paid invoices found.")

# ==========================================
# 2. PRODUCTS & STOCK MANAGEMENT
# ==========================================
elif selected == "Products & Stock":
    st.title("📦 Products & Digital Inventory")
    st.markdown("Manage your digital catalog and upload license keys or deliverables.")
    st.markdown("---")

    tab1, tab2 = st.tabs(["Active Catalog", "Add New Product / Stock"])

    with tab1:
        products_df = get_data("SELECT * FROM products")
        if not products_df.empty:
            st.dataframe(products_df, use_container_width=True)
        else:
            st.info("No products available.")

    with tab2:
        st.subheader("Create a New Product")
        with st.form("new_product_form"):
            prod_name = st.text_input("Product Name")
            prod_desc = st.text_area("Description")
            prod_price = st.number_input("Price (USD)", min_value=0.0, step=0.10)
            submitted = st.form_submit_button("Add Product")
            
            if submitted and prod_name:
                conn = get_turso_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO products (name, description, price_usd) VALUES (?, ?, ?)", (prod_name, prod_desc, prod_price))
                conn.commit()
                conn.close()
                st.success(f"Product '{prod_name}' successfully added to Turso cloud!")
                st.rerun()

        st.markdown("---")
        st.subheader("Add Stock / Deliverables to Product")
        products_list = get_data("SELECT product_id, name FROM products")
        
        if not products_list.empty:
            product_options = {row['name']: row['product_id'] for _, row in products_list.iterrows()}
            selected_prod_name = st.selectbox("Select Product", list(product_options.keys()))
            selected_prod_id = product_options[selected_prod_name]
            
            stock_content = st.text_area("Deliverables (Put each account/key/link on a new line)")
            if st.button("Upload Stock"):
                if stock_content.strip():
                    lines = [line.strip() for line in stock_content.split("\n") if line.strip()]
                    conn = get_turso_connection()
                    data_to_insert = [(selected_prod_id, line) for line in lines]
                    conn.executemany("INSERT INTO inventory (product_id, content) VALUES (?, ?)", data_to_insert)
                    conn.commit()
                    conn.close()
                    st.success(f"Successfully added {len(lines)} stock items to {selected_prod_name}!")
                else:
                    st.warning("Please enter valid inventory text.")
        else:
            st.info("Create a product first before adding stock.")

# ==========================================
# 3. ORDERS
# ==========================================
elif selected == "Orders":
    st.title("🛒 Complete Order History")
    st.markdown("View all fulfillment logs and delivered digital goods.")
    st.markdown("---")
    
    orders_df = get_data("SELECT * FROM orders ORDER BY purchased_at DESC")
    if not orders_df.empty:
        st.dataframe(orders_df, use_container_width=True)
    else:
        st.info("No orders found in the database.")

# ==========================================
# 4. USERS & BALANCES
# ==========================================
elif selected == "Users & Balances":
    st.title("👥 Customer Profiles & Balances")
    st.markdown("Inspect registered customers and adjust wallet funds.")
    st.markdown("---")

    users_df = get_data("SELECT * FROM users ORDER BY registered_at DESC")
    if not users_df.empty:
        st.dataframe(users_df, use_container_width=True)
        
        st.markdown("---")
        st.subheader("Modify User Wallet Balance")
        with st.form("balance_form"):
            target_user_id = st.number_input("User ID", min_value=1, step=1)
            amount_adjustment = st.number_input("Amount to Add/Deduct (+ or - USD)", value=5.0, step=1.0)
            update_btn = st.form_submit_button("Update Balance")
            
            if update_btn:
                success = execute_query("UPDATE users SET balance_usd = balance_usd + ? WHERE user_id = ?", (amount_adjustment, target_user_id))
                if success:
                    st.success(f"Successfully adjusted balance for User {target_user_id} by ${amount_adjustment}!")
                    st.rerun()
                else:
                    st.error("Failed to update user balance.")
    else:
        st.info("No registered users found.")

# ==========================================
# 5. INVOICES
# ==========================================
elif selected == "Invoices":
    st.title("💳 CryptoBot Invoices")
    st.markdown("Monitor user payment transactions and invoice statuses.")
    st.markdown("---")

    invoices_df = get_data("SELECT * FROM invoices ORDER BY created_at DESC")
    if not invoices_df.empty:
        st.dataframe(invoices_df, use_container_width=True)
    else:
        st.info("No invoices logged yet.")