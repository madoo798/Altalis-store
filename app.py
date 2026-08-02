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
    page_icon="🗝️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# THEME
# A "ledger & vault" aesthetic
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

    :root {
        --bg:       #0B0E13;
        --panel:     #12161E;
        --panel-2:   #171C26;
        --hairline:  #2A3140;
        --brass:     #C9A227;
        --brass-dim: #8A7220;
        --teal:      #4E9B94;
        --text:      #E4E6EA;
        --text-dim:  #8A93A3;
        --danger:    #C6564B;
    }

    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
        color: var(--text);
    }

    .stApp {
        background: radial-gradient(circle at 15% 0%, #141A24 0%, var(--bg) 55%);
    }

    /* ---------- Headings ---------- */
    h1, h2, h3 {
        font-family: 'Fraunces', serif !important;
        font-weight: 600 !important;
        letter-spacing: 0.2px;
        color: var(--text) !important;
    }
    h1 { border-bottom: 1px solid var(--hairline); padding-bottom: 14px; }

    /* Eyebrow-style captions under headings */
    .eyebrow {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 12px;
        letter-spacing: 2.5px;
        text-transform: uppercase;
        color: var(--brass);
        margin-bottom: 4px;
    }

    /* ---------- Sidebar ---------- */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #10141C 0%, #0B0E13 100%);
        border-right: 1px solid var(--hairline);
    }
    section[data-testid="stSidebar"] .stCaption, section[data-testid="stSidebar"] p {
        color: var(--text-dim) !important;
    }

    /* ---------- Metric cards ---------- */
    div[data-testid="stMetric"] {
        background: linear-gradient(160deg, var(--panel) 0%, var(--panel-2) 100%);
        border: 1px solid var(--hairline);
        border-top: 2px solid var(--brass);
        padding: 18px 20px;
        border-radius: 6px;
    }
    div[data-testid="stMetricLabel"] {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 11px !important;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: var(--text-dim) !important;
    }
    div[data-testid="stMetricValue"] {
        font-family: 'Fraunces', serif !important;
        color: var(--text) !important;
    }

    /* ---------- Hairline divider ---------- */
    hr, div[data-testid="stMarkdownContainer"] hr {
        border: none;
        border-top: 1px solid var(--hairline);
        margin: 22px 0;
    }

    /* ---------- Tabs ---------- */
    button[data-baseweb="tab"] {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 12px;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: var(--text-dim);
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: var(--brass) !important;
    }
    div[data-baseweb="tab-highlight"] {
        background-color: var(--brass) !important;
    }

    /* ---------- Dataframes / tables ---------- */
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--hairline);
        border-radius: 6px;
        overflow: hidden;
    }
    div[data-testid="stDataFrame"] * {
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 13px !important;
    }

    /* ---------- Forms & inputs ---------- */
    div[data-testid="stForm"] {
        background: var(--panel);
        border: 1px solid var(--hairline);
        border-radius: 8px;
        padding: 22px;
    }
    .stTextInput input, .stTextArea textarea, .stNumberInput input, div[data-baseweb="select"] > div {
        background-color: var(--panel-2) !important;
        border: 1px solid var(--hairline) !important;
        color: var(--text) !important;
        border-radius: 5px !important;
    }

    /* ---------- Buttons ---------- */
    .stButton button, .stFormSubmitButton button {
        background: linear-gradient(160deg, var(--brass) 0%, var(--brass-dim) 100%);
        color: #12161E;
        font-weight: 600;
        border: none;
        border-radius: 5px;
        padding: 8px 18px;
        transition: filter 0.15s ease;
    }
    .stButton button:hover, .stFormSubmitButton button:hover {
        filter: brightness(1.12);
        color: #0B0E13;
    }

    /* ---------- Alerts ---------- */
    div[data-testid="stAlert"] {
        border-radius: 6px;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 13px;
    }

    /* ---------- Section labels ---------- */
    .stSubheader, h3 {
        margin-top: 6px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# TURSO CLOUD DATABASE CONNECTION & SETUP
# ==========================================
TURSO_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

if not TURSO_URL or not TURSO_TOKEN:
    st.error(
        "⚠️ Missing database credentials. Set the `TURSO_DATABASE_URL` and "
        "`TURSO_AUTH_TOKEN` environment variables before running this app "
        "(never hardcode credentials in source code)."
    )
    st.stop()

def get_turso_connection():
    """Create a secure connection to the Turso cloud database."""
    if TURSO_URL.startswith("libsql://") or TURSO_URL.startswith("https://"):
        return libsql.connect(TURSO_URL, auth_token=TURSO_TOKEN)
    else:
        return libsql.connect(TURSO_URL)

@st.cache_resource
def init_cloud_db():
    """Automatically create database tables in Turso if they don't exist.
    Cached so it only runs ONCE when the app starts."""
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

def get_data(query: str, params: tuple = ()) -> pd.DataFrame:
    """Fetch query results safely using parameterized queries."""
    try:
        conn = get_turso_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
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

def get_single_value(query: str, params: tuple = ()) -> float:
    """Fetch a single numeric aggregate value safely."""
    try:
        conn = get_turso_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        conn.close()
        return row[0] if row and row[0] is not None else 0.0
    except Exception:
        return 0.0

# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown(
        "<div style='font-family:Fraunces,serif;font-size:26px;font-weight:600;"
        "color:#E4E6EA;letter-spacing:0.5px;'>🗝️ Altalis <span style='color:#C9A227;'>&</span> Celesta</div>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<div class='eyebrow' style='margin-top:4px;'>Cloud Admin · Turso</div>",
        unsafe_allow_html=True
    )
    st.markdown("<hr>", unsafe_allow_html=True)

    selected = option_menu(
        menu_title=None,
        options=["Overview", "Products & Stock", "Orders", "Users & Balances", "Invoices"],
        icons=["speedometer2", "box-seam", "receipt", "people", "wallet2"],
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#C9A227", "font-size": "16px"},
            "nav-link": {
                "font-family": "Inter, sans-serif",
                "font-size": "14px",
                "text-align": "left",
                "margin": "2px 0",
                "border-radius": "5px",
                "--hover-color": "#171C26",
                "color": "#8A93A3",
            },
            "nav-link-selected": {
                "background-color": "#171C26",
                "color": "#E4E6EA",
                "border-left": "2px solid #C9A227",
            },
        }
    )

# ==========================================
# 1. OVERVIEW PAGE
# ==========================================
if selected == "Overview":
    st.markdown("<div class='eyebrow'>Store Performance</div>", unsafe_allow_html=True)
    st.title("Overview")
    st.markdown("Real-time telemetry synced securely via your Turso cloud database.")
    st.markdown("<hr>", unsafe_allow_html=True)

    # ONE network request for all metrics
    combined_query = """
    SELECT 
        (SELECT COUNT(*) FROM users) AS total_users,
        (SELECT COALESCE(SUM(amount_usd), 0) FROM invoices WHERE status = 'paid') AS total_revenue,
        (SELECT COUNT(*) FROM orders) AS total_orders,
        (SELECT COUNT(*) FROM products WHERE is_active = 1) AS active_products
    """
    
    metrics_df = get_data(combined_query)
    
    if not metrics_df.empty:
        metrics = metrics_df.iloc[0]
        total_users = metrics['total_users']
        total_revenue = metrics['total_revenue']
        total_orders = metrics['total_orders']
        active_products = metrics['active_products']
    else:
        total_users = total_revenue = total_orders = active_products = 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Users", f"{int(total_users)}")
    with col2:
        st.metric("Total Revenue", f"${total_revenue:.2f}")
    with col3:
        st.metric("Completed Orders", f"{int(total_orders)}")
    with col4:
        st.metric("Active Products", f"{int(active_products)}")

    st.markdown("<hr>", unsafe_allow_html=True)

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
    st.markdown("<div class='eyebrow'>Catalog</div>", unsafe_allow_html=True)
    st.title("Products & Digital Inventory")
    st.markdown("Manage your digital catalog and upload license keys or deliverables.")
    st.markdown("<hr>", unsafe_allow_html=True)

    # Added Tab 3 here
    tab1, tab2, tab3 = st.tabs(["Active Catalog", "Add New Product / Stock", "Edit Product"])

    with tab1:
        products_df = get_data("SELECT * FROM products")
        if not products_df.empty:
            st.dataframe(products_df, use_container_width=True)
        else:
            st.info("No products available.")

    with tab2:
        col_prod, col_stock = st.columns(2)
        
        with col_prod:
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

        with col_stock:
            st.subheader("📦 Bulk Vault Restock")
            products_list = get_data("SELECT product_id, name FROM products")

            if not products_list.empty:
                with st.form("bulk_stock_form"):
                    product_options = {row['name']: row['product_id'] for _, row in products_list.iterrows()}
                    selected_prod_name = st.selectbox("Select Target Product", list(product_options.keys()))
                    selected_prod_id = product_options[selected_prod_name]

                    stock_content = st.text_area("Paste Digital Keys/Links (One per line)")
                    
                    if st.form_submit_button("Secure Inventory"):
                        if stock_content.strip():
                            lines = [line.strip() for line in stock_content.split("\n") if line.strip()]
                            conn = get_turso_connection()
                            data_to_insert = [(selected_prod_id, line) for line in lines]
                            conn.executemany("INSERT INTO inventory (product_id, content) VALUES (?, ?)", data_to_insert)
                            conn.commit()
                            conn.close()
                            st.success(f"Successfully locked {len(lines)} stock items to {selected_prod_name}!")
                        else:
                            st.warning("Please paste at least one valid key.")
            else:
                st.info("Create a product first before adding stock.")

    with tab3:
        st.subheader("Edit Existing Product")
        
        # Fetch products including their current descriptions
        edit_products_list = get_data("SELECT product_id, name, description FROM products")
        
        if not edit_products_list.empty:
            # Map product names to their ID and current description
            edit_prod_dict = {row['name']: (row['product_id'], row['description']) for _, row in edit_products_list.iterrows()}
            
            selected_edit_prod = st.selectbox("Select Product to Edit", list(edit_prod_dict.keys()))
            prod_id_to_edit, current_desc = edit_prod_dict[selected_edit_prod]
            
            with st.form("edit_desc_form"):
                # Pre-fill the text area with the existing database description
                new_desc = st.text_area("Product Description", value=current_desc if current_desc else "", height=250)
                submit_edit = st.form_submit_button("Save Changes")
                
                if submit_edit:
                    success = execute_query("UPDATE products SET description = ? WHERE product_id = ?", (new_desc, prod_id_to_edit))
                    if success:
                        st.success(f"✅ Successfully updated the description for {selected_edit_prod}!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update the description in the database.")
        else:
            st.info("No active products available to edit.")

# ==========================================
# 3. ORDERS (FULFILLMENT & GIFTING)
# ==========================================
elif selected == "Orders":
    st.markdown("<div class='eyebrow'>Fulfillment Log</div>", unsafe_allow_html=True)
    st.title("Order & Fulfillment Management")
    st.markdown("View past orders or manually gift a product key to a specific user.")
    st.markdown("<hr>", unsafe_allow_html=True)

    tab_log, tab_gift = st.tabs(["Order History", "Manual Fulfill & Gift"])

    with tab_log:
        orders_df = get_data("SELECT * FROM orders ORDER BY purchased_at DESC LIMIT 100")
        if not orders_df.empty:
            st.dataframe(orders_df, use_container_width=True)
        else:
            st.info("No orders found in the database.")
            
    with tab_gift:
        st.subheader("Manually Fulfill or Gift an Order")
        st.markdown("Select a user and a product. This will pull **one unit** from your unsold stock, assign it to the user, and reveal the key so you can DM it to them. **(Their wallet balance will NOT be charged)**.")
        
        with st.form("manual_fulfill_form"):
            target_user = st.number_input("Customer Telegram ID", min_value=1, step=1)
            
            # Get products list for dropdown
            products_list = get_data("SELECT product_id, name FROM products WHERE is_active = 1")
            
            if not products_list.empty:
                prod_dict = {row['name']: row['product_id'] for _, row in products_list.iterrows()}
                selected_prod = st.selectbox("Select Product to Give", list(prod_dict.keys()))
                prod_id = prod_dict[selected_prod]
            else:
                st.warning("No active products available.")
                prod_id = None
                
            submit_gift = st.form_submit_button("Grant Access & Extract Key")
            
            if submit_gift and prod_id:
                conn = get_turso_connection()
                cursor = conn.cursor()
                
                # 1. Grab one unsold key from inventory
                cursor.execute("SELECT item_id, content FROM inventory WHERE product_id = ? AND (is_sold = 0 OR is_sold IS NULL) LIMIT 1", (prod_id,))
                stock_item = cursor.fetchone()
                
                if stock_item:
                    item_id, delivered_content = stock_item
                    
                    # 2. Mark that specific item as sold
                    cursor.execute("UPDATE inventory SET is_sold = 1 WHERE item_id = ?", (item_id,))
                    
                    # 3. Log to standard `orders` table
                    cursor.execute("INSERT INTO orders (user_id, product_id, delivered_content) VALUES (?, ?, ?)", (target_user, prod_id, delivered_content))
                    
                    # 4. Attempt to log to `customer_orders` (the table used by the Bot's /myorders command)
                    cursor.execute("SELECT price_usd FROM products WHERE product_id = ?", (prod_id,))
                    price_row = cursor.fetchone()
                    price = price_row[0] if price_row else 0.0
                    try:
                        cursor.execute("INSERT INTO customer_orders (user_id, product_name, price_usd, deliverable) VALUES (?, ?, ?, ?)", (target_user, selected_prod, price, delivered_content))
                    except Exception:
                        pass # Silently pass if this table doesn't exist yet
                        
                    conn.commit()
                    st.success(f"🎉 Successfully fulfilled! {selected_prod} assigned to User {target_user}.")
                    st.info(f"🔑 **Extracted Key/Link:** `{delivered_content}`\n\n*(Copy this key and DM it to the user)*")
                else:
                    st.error(f"❌ OUT OF STOCK: There are no unsold keys left for {selected_prod}.")
                    
                conn.close()

# ==========================================
# 4. USERS & BALANCES
# ==========================================
elif selected == "Users & Balances":
    st.markdown("<div class='eyebrow'>Customer Ledger</div>", unsafe_allow_html=True)
    st.title("Customer Profiles & Balances")
    st.markdown("Inspect registered customers and adjust wallet funds.")
    st.markdown("<hr>", unsafe_allow_html=True)

    # Fixed explicit column selection query to prevent table column shifting
    users_df = get_data("SELECT user_id, username, balance_usd, registered_at FROM users ORDER BY registered_at DESC LIMIT 100")
    if not users_df.empty:
        st.dataframe(users_df, use_container_width=True)

        st.markdown("<hr>", unsafe_allow_html=True)
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
    st.markdown("<div class='eyebrow'>Payments</div>", unsafe_allow_html=True)
    st.title("CryptoBot Invoices")
    st.markdown("Monitor user payment transactions and invoice statuses.")
    st.markdown("<hr>", unsafe_allow_html=True)

    invoices_df = get_data("SELECT * FROM invoices ORDER BY created_at DESC LIMIT 100")
    if not invoices_df.empty:
        st.dataframe(invoices_df, use_container_width=True)
    else:
        st.info("No invoices logged yet.")