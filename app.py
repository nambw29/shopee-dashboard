import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# Cấu hình trang
st.set_page_config(
    page_title="Shopee Affiliate Analytics Dashboard by BLACKWHITE29",
    layout="wide",
    page_icon="🧧"
)

# CSS tùy chỉnh vùng upload
st.markdown("""
    <style>
    [data-testid="stFileUploaderDropzoneInstructions"] > div > span {display: none;}
    [data-testid="stFileUploaderDropzoneInstructions"] > div::before {
        content: "Kéo và thả tệp vào đây";
        display: block;
        font-size: 1.2em;
        font-weight: bold;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] > div::after {
        content: "Hỗ trợ tệp .CSV";
        display: block;
        font-size: 0.8em;
    }
    .stFileUploader section button {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# Hàm định dạng tiền
def format_currency(value):
    return f"{int(round(value, 0)):,}".replace(',', '.') + " ₫"

# Load và xử lý dữ liệu
@st.cache_data
def load_data(file):
    df = None
    try:
        df = pd.read_csv(file, encoding='utf-8-sig')
    except:
        file.seek(0)
        try:
            df = pd.read_csv(file, encoding='utf-8')
        except:
            file.seek(0)
            df = pd.read_csv(file, encoding='latin1')

    if df is None or df.empty:
        st.error("File CSV rỗng hoặc không có dữ liệu.")
        return None

    try:
        df['Thời Gian Đặt Hàng'] = pd.to_datetime(df['Thời Gian Đặt Hàng'], errors='coerce')
        df['Ngày'] = df['Thời Gian Đặt Hàng'].dt.date

        numeric_cols = [
            'Giá trị đơn hàng (₫)', 'Tổng hoa hồng đơn hàng(₫)',
            'Hoa hồng Shopee trên sản phẩm(₫)', 'Hoa hồng Xtra trên sản phẩm(₫)',
            'Giá(₫)', 'Số lượng'
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace(',', '').str.replace('₫', ''),
                    errors='coerce'
                ).fillna(0)

        # Phân loại nguồn
        def classify_source(row):
            k = str(row.get('Kênh', '')).strip()
            if k in ['Facebook', 'Instagram', 'Zalo']:
                return 'Social'
            return 'Others'

        df['Phân loại nguồn'] = df.apply(classify_source, axis=1)

        return df

    except Exception as e:
        st.error(f"Lỗi xử lý dữ liệu: {e}")
        return None

# =============================================
# GIAO DIỆN
# =============================================

st.title("🧧 Shopee Affiliate Analytics Dashboard by BLACKWHITE29")

col_upload, col_date = st.columns([1, 1])

with col_upload:
    st.markdown("### Tải lên file dữ liệu")
    uploaded_file = st.file_uploader("", type=["csv"], label_visibility="collapsed")

with col_date:
    st.markdown("### Chọn khoảng thời gian")
    date_range = None

    if uploaded_file is not None:
        df_temp = load_data(uploaded_file)
        if df_temp is not None:
            # Xử lý trường hợp min_date / max_date là NaT
            if pd.isna(df_temp['Ngày']).all():
                st.error("Không có dữ liệu ngày hợp lệ trong file.")
            else:
                min_date = df_temp['Ngày'].min()
                max_date = df_temp['Ngày'].max()
                today = datetime.date.today()

                # Đảm bảo min_date và max_date không phải NaT
                min_date = min_date if pd.notna(min_date) else today
                max_date = max_date if pd.notna(max_date) else today

                options = {
                    "Ngày cập nhật lần cuối": (max_date, max_date),
                    "7 ngày qua": (today - datetime.timedelta(days=7), today),
                    "15 ngày qua": (today - datetime.timedelta(days=15), today),
                    "30 ngày qua": (today - datetime.timedelta(days=30), today),
                    "Tháng này": (datetime.date(today.year, today.month, 1), today),
                    "Tháng trước": (
                        datetime.date(
                            today.year - 1 if today.month == 1 else today.year,
                            12 if today.month == 1 else today.month - 1,
                            1
                        ),
                        datetime.date(today.year, today.month, 1) - datetime.timedelta(days=1)
                    ),
                    "Từ trước đến nay": (min_date, max_date)
                }

                choice = st.selectbox("Lựa chọn:", list(options.keys()), index=0, label_visibility="collapsed")
                date_range = options[choice]
                st.info(f"📅 {date_range[0]:%d/%m/%Y} – {date_range[1]:%d/%m/%Y}")
        else:
            st.error("Không đọc được file dữ liệu.")

if uploaded_file is not None:
    df = load_data(uploaded_file)
    if df is not None:
        if date_range is not None:
            df_filtered = df[(df['Ngày'] >= date_range[0]) & (df['Ngày'] <= date_range[1])]
        else:
            df_filtered = df

        st.markdown("---")

        # 1. Tổng quan
        st.header("1. Thống kê tổng quan")

        total_gmv = df_filtered['Giá trị đơn hàng (₫)'].sum()
        total_comm = df_filtered['Tổng hoa hồng đơn hàng(₫)'].sum()
        total_orders = df_filtered['ID đơn hàng'].nunique()

        cols = st.columns(3)
        cols[0].metric("Tổng GMV", format_currency(total_gmv))
        cols[1].metric("Tổng Hoa hồng", format_currency(total_comm))
        cols[2].metric("Tổng đơn", f"{total_orders:,}".replace(",", "."))

        st.markdown("---")

        # 5. Top 10 sản phẩm - Tên là link
        st.header("5. Top 10 sản phẩm nhiều đơn nhất")

        if 'Tên Item' in df_filtered.columns and 'Shop id' in df_filtered.columns and 'Item id' in df_filtered.columns:
            product_stats = df_filtered.groupby(['Tên Item', 'Shop id', 'Item id']).agg({
                'Giá trị đơn hàng (₫)': 'sum',
                'ID đơn hàng': 'count',
                'Tổng hoa hồng đơn hàng(₫)': 'sum'
            }).rename(columns={
                'Giá trị đơn hàng (₫)': 'GMV',
                'ID đơn hàng': 'Số_đơn',
                'Tổng hoa hồng đơn hàng(₫)': 'Hoa_hồng'
            }).reset_index()

            product_stats['Tỉ lệ HH (%)'] = (product_stats['Hoa_hồng'] / product_stats['GMV'] * 100).round(2)
            top_products = product_stats.nlargest(10, 'Số_đơn').reset_index(drop=True)

            if not top_products.empty:
                top_products['Link'] = top_products.apply(
                    lambda r: f"https://shopee.vn/product/{r['Shop id']}/{r['Item id']}", axis=1
                )

                display_df = top_products[['Tên Item', 'GMV', 'Số_đơn', 'Hoa_hồng', 'Tỉ lệ HH (%)']].copy()
                display_df.rename(columns={'Tên Item': 'Tên sản phẩm'}, inplace=True)
                display_df['GMV'] = display_df['GMV'].apply(format_currency)
                display_df['Hoa_hồng'] = display_df['Hoa_hồng'].apply(format_currency)
                display_df['Số_đơn'] = display_df['Số_đơn'].apply(lambda x: f"{x:,}".replace(',', '.'))

                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Tên sản phẩm": st.column_config.LinkColumn(
                            "Tên sản phẩm",
                            help="Nhấn để xem sản phẩm",
                            width="large"
                        ),
                        "GMV": "Tổng GMV",
                        "Số_đơn": "Số đơn",
                        "Hoa_hồng": "Hoa hồng",
                        "Tỉ lệ HH (%)": st.column_config.NumberColumn(format="%.2f")
                    }
                )
            else:
                st.info("Không có dữ liệu sản phẩm trong khoảng thời gian.")
        else:
            st.warning("File thiếu cột cần thiết cho top sản phẩm (Tên Item, Shop id, Item id)")

        st.markdown("---")

        # 6. Top 10 shop - Tên shop là link
        st.header("6. Top 10 shop có nhiều đơn nhất")

        if 'Tên Shop' in df_filtered.columns and 'Shop id' in df_filtered.columns:
            shop_stats = df_filtered.groupby(['Tên Shop', 'Shop id']).agg({
                'Giá trị đơn hàng (₫)': 'sum',
                'ID đơn hàng': 'nunique',
                'Tổng hoa hồng đơn hàng(₫)': 'sum'
            }).rename(columns={
                'Giá trị đơn hàng (₫)': 'GMV',
                'ID đơn hàng': 'Số_đơn',
                'Tổng hoa hồng đơn hàng(₫)': 'Hoa_hồng'
            }).reset_index()

            shop_stats['Tỉ lệ HH (%)'] = (shop_stats['Hoa_hồng'] / shop_stats['GMV'] * 100).round(2)
            top_shops = shop_stats.nlargest(10, 'Số_đơn').reset_index(drop=True)

            if not top_shops.empty:
                top_shops['Link'] = top_shops['Shop id'].apply(lambda x: f"https://shopee.vn/shop/{x}")

                display_shop = top_shops[['Tên Shop', 'GMV', 'Số_đơn', 'Hoa_hồng', 'Tỉ lệ HH (%)']].copy()
                display_shop['GMV'] = display_shop['GMV'].apply(format_currency)
                display_shop['Hoa_hồng'] = display_shop['Hoa_hồng'].apply(format_currency)
                display_shop['Số_đơn'] = display_shop['Số_đơn'].apply(lambda x: f"{x:,}".replace(',', '.'))

                st.dataframe(
                    display_shop,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Tên Shop": st.column_config.LinkColumn(
                            "Tên Shop",
                            help="Nhấn để xem shop",
                            width="large"
                        ),
                        "GMV": "Tổng GMV",
                        "Số_đơn": "Số đơn",
                        "Hoa_hồng": "Hoa hồng",
                        "Tỉ lệ HH (%)": st.column_config.NumberColumn(format="%.2f")
                    }
                )
            else:
                st.info("Không có dữ liệu shop trong khoảng thời gian.")
        else:
            st.warning("File thiếu cột cần thiết cho top shop (Tên Shop, Shop id)")

        st.markdown("---")
        st.success("Dashboard đã chạy xong phần chính. Nếu cần thêm biểu đồ hoặc chi tiết đơn hàng, báo mình nhé Nam!")

    else:
        st.error("Không thể xử lý file dữ liệu.")
