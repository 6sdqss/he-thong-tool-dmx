import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
import json
import os
from requests.utils import cookiejar_from_dict

# ==========================================
# CẤU HÌNH HEADER & THÔNG SỐ CHUNG
# ==========================================
st.set_page_config(page_title="Hệ Thống Tool ĐỨC", page_icon="💎", layout="wide")

# TÀI KHOẢN ĐĂNG NHẬP
USERS = {"ducadmin": "matkhau123", "nhanvien1": "123456"}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}

# ==========================================
# KHU VỰC 1: HỆ THỐNG ĐỌC COOKIE TỰ ĐỘNG
# ==========================================
def get_session():
    """Hàm nạp Cookie từ 2 file JSON riêng biệt để vượt tường lửa"""
    session = requests.Session()
    session.headers.update(HEADERS)
    
    all_cookies = {}
    
    # Đọc Cookie DMX
    if os.path.exists("cookies_dmx.json"):
        try:
            with open("cookies_dmx.json", "r", encoding="utf-8") as f:
                for c in json.load(f):
                    if c.get("name") and c.get("value"): 
                        all_cookies[c.get("name")] = c.get("value")
        except Exception as e:
            st.error(f"Lỗi đọc cookies_dmx.json: {e}")
            
    # Đọc Cookie TGDD
    if os.path.exists("cookies_tgdd.json"):
        try:
            with open("cookies_tgdd.json", "r", encoding="utf-8") as f:
                for c in json.load(f):
                    if c.get("name") and c.get("value"): 
                        all_cookies[c.get("name")] = c.get("value")
        except Exception as e:
            st.error(f"Lỗi đọc cookies_tgdd.json: {e}")
            
    session.cookies = cookiejar_from_dict(all_cookies)
    return session

# ==========================================
# KHU VỰC 2: CÁC HÀM XỬ LÝ LẤY ẢNH (GIỮ NGUYÊN BẢN)
# ==========================================
def extract_simage_thumb(simage_str):
    if not simage_str: return None
    try:
        images = json.loads(simage_str)
        if not isinstance(images, list): return None
        thumb_image = None
        for img in images:
            if isinstance(img, dict) and img.get("PictureUrl"):
                if img.get("IsThumb") is True: return img["PictureUrl"]
                if thumb_image is None: thumb_image = img["PictureUrl"]
        return thumb_image
    except:
        if simage_str.startswith(("http", "//", "/")): return simage_str
        return None

def clean_image_url(url):
    if not url: return url
    cleaned = re.sub(r'-\d+x\d+(?=\.(?:jpg|jpeg|png))', '', url)
    if cleaned.startswith("//"): return "https:" + cleaned
    elif cleaned.startswith("/"): return "https://cdnv2.tgdd.vn" + cleaned
    return cleaned

def fetch_by_page(session, product_id, domain):
    short_url = f"https://www.{domain}/sp-{product_id}"
    try:
        r = session.get(short_url, headers=HEADERS, allow_redirects=True, timeout=12)
        if r.status_code != 200: return None, None, f"HTTP {r.status_code}"
        html = r.text
        m = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', html, re.I)
        if m: return r.url, m.group(1), "OK(Page-og)"
        m2 = re.search(r'(https?://[^"\']+(?:cdnv2.tgdd.vn|cdn.tgdd.vn|cdnv2.tgdd|tgdd.vn)[^"\']+\.(?:png|jpg|jpeg))', html, re.I)
        if m2: return r.url, m2.group(1), "OK(Page-find)"
        return r.url, None, "NoImageFound"
    except Exception as e: return None, None, f"Error: {e}"

def fetch_by_api(session, product_id, domain):
    api_url = f"https://www.{domain}/apiweb/productdetails?productId={product_id}"
    try:
        r = session.get(api_url, headers=HEADERS, timeout=10)
        if r.status_code != 200: return None, None, f"API HTTP {r.status_code}"
        data = r.json()
        seo = data.get("SeoUrl") or data.get("SeoUrlRaw")
        pic = data.get("PictureUrl") or data.get("ImagePath")
        simage = data.get("SIMAGE") or data.get("simage")
        
        if not seo and isinstance(data, dict):
            for k in ("data", "product", "productDetails"):
                if k in data and isinstance(data[k], dict):
                    dd = data[k]
                    seo = seo or dd.get("SeoUrl")
                    pic = pic or dd.get("PictureUrl")
                    simage = simage or dd.get("SIMAGE")
                    if seo: break
                    
        thumb_from_simage = extract_simage_thumb(simage) if simage else None
        if thumb_from_simage: pic = thumb_from_simage
            
        if seo:
            final_url = f"https://www.{domain}" + seo if seo.startswith("/") else seo
            status = "OK" if simage and pic == thumb_from_simage else "OK"
            return final_url, pic or "", status
        return None, pic or "", "Lỗi API"
    except Exception as e: return None, None, f"API_error: {e}"

# ==========================================
# KHU VỰC 3: HỆ THỐNG ĐĂNG NHẬP & PHÂN QUYỀN
# ==========================================
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align: center; color: #1A237E;'>HỆ THỐNG QUẢN LÝ NỘI DUNG</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Vui lòng đăng nhập để tiếp tục</p>", unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("👤 Tên đăng nhập")
            password = st.text_input("🔑 Mật khẩu", type="password")
            if st.form_submit_button("🚀 ĐĂNG NHẬP", use_container_width=True):
                if username in USERS and USERS[username] == password:
                    st.session_state["logged_in"] = True
                    st.session_state["user"] = username
                    st.rerun()
                else: 
                    st.error("❌ Sai tài khoản hoặc mật khẩu!")
    st.stop()

# --- SIDEBAR ---
st.sidebar.markdown(f"### 👋 Xin chào, **{st.session_state['user'].upper()}**!")
st.sidebar.markdown("---")

# Phân quyền hiển thị Menu
if st.session_state["user"] == "ducadmin":
    menu_options = [
        "🏠 1. Trang chủ", 
        "📸 2. Lấy Thumb DMX", 
        "📸 3. Lấy Thumb TGDD",
        "📊 4. Lọc File (Google Sheet)"
    ]
else:
    # Nhân viên không thấy Lọc File
    menu_options = [
        "🏠 1. Trang chủ", 
        "📸 2. Lấy Thumb DMX", 
        "📸 3. Lấy Thumb TGDD"
    ]

menu = st.sidebar.radio("📌 TÍNH NĂNG CHÍNH", menu_options)

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Đăng xuất", use_container_width=True):
    st.session_state["logged_in"] = False
    st.rerun()

# ==========================================
# KHU VỰC 4: GIAO DIỆN CHÍNH
# ==========================================

# --- TRANG CHỦ ---
if "1. Trang chủ" in menu:
    st.title("🌟 TỔNG QUAN HỆ THỐNG")
    if st.session_state["user"] == "ducadmin":
        st.info("🔥 **Tài khoản Admin:** Bạn có toàn quyền sử dụng tất cả các công cụ, bao gồm cả Tool Lọc File (Google Sheet).")
    else:
        st.info("👥 **Tài khoản Nhân viên:** Bạn được cấp quyền sử dụng các công cụ Lấy ảnh Thumbnail.")
        
    st.markdown("""
    ### 💡 Cập nhật mới nhất:
    - **Giao diện tối giản:** Đẹp hơn, trực quan hơn, chạy cực nhanh.
    - **Tính năng Copy 1-Click:** Không cần tải Excel nếu không muốn. Cứ bấm nút Copy ở góc phải màn hình kết quả là dán thẳng vào Sheet/Excel chuẩn 100% (chia đúng cột).
    - **Tự động phân luồng Cookie:** Hệ thống tự động mở khóa bảo mật của TGDD và DMX.
    """)

# --- TOOL LẤY THUMB DMX & TGDD ---
elif "Lấy Thumb" in menu:
    domain = "dienmayxanh.com" if "DMX" in menu else "thegioididong.com"
    logo_color = "#0088FF" if "DMX" in menu else "#FFCA28"
    
    st.markdown(f"<h2 style='color: {logo_color};'>📸 Tool Quét Link Ảnh Thumbnail ({domain.upper()})</h2>", unsafe_allow_html=True)
    st.markdown("Nhập danh sách ID sản phẩm (mỗi ID 1 dòng) để lấy Link gốc và Link ảnh chất lượng cao.")
    
    col1, col2 = st.columns([1, 2.5])
    
    with col1:
        raw_input = st.text_area("✍️ Dán danh sách ID vào đây:", height=300)
        btn_run = st.button("🚀 QUÉT DỮ LIỆU", type="primary", use_container_width=True)

    with col2:
        if btn_run:
            if not raw_input.strip():
                st.warning("⚠️ Vui lòng nhập ít nhất 1 ID!")
            else:
                ids = [l.strip() for l in raw_input.splitlines() if l.strip()]
                results = []
                
                progress_text = st.empty()
                progress_bar = st.progress(0)
                session = get_session()
                
                for i, pid in enumerate(ids):
                    progress_text.markdown(f"⏳ Đang quét: **{pid}** ({i+1}/{len(ids)})")
                    mnum = re.search(r'(\d+)(?!.*\d)', pid)
                    pid_num = mnum.group(1) if mnum else pid
                    
                    final_url, thumb, status = None, None, "Start"
                    f_url, t_img, s = fetch_by_page(session, pid_num, domain)
                    
                    if s.startswith("OK(Page-og"):
                        final_url, thumb, status = f_url, t_img, "OK"
                    else:
                        a_url, a_img, a_s = fetch_by_api(session, pid_num, domain)
                        final_url = final_url or a_url or f_url
                        thumb = a_img or t_img
                        status = "OK" if thumb else "Lỗi"
                        
                    thumb_clean = clean_image_url(thumb) if thumb else ""
                    if not final_url: final_url = f"https://www.{domain}/sp-{pid_num}"
                    out_status = "OK" if thumb_clean else "Không có ảnh"
                    
                    results.append({
                        "ID": pid_num, 
                        "Link SP": final_url, 
                        "Link Ảnh": thumb_clean, 
                        "Trạng Thái": out_status
                    })
                    
                    progress_bar.progress((i + 1) / len(ids))
                    time.sleep(0.1) # Nghỉ để tránh bị block
                
                progress_text.success("✅ QUÉT HOÀN TẤT!")
                
                # Tạo giao diện kết quả đẹp
                df = pd.DataFrame(results)
                
                # Tab để hiển thị
                tab_table, tab_copy = st.tabs(["📋 Bảng dữ liệu", "📝 Nút Copy Nhanh (Dán Excel)"])
                
                with tab_table:
                    st.dataframe(df, use_container_width=True)
                    st.download_button("📥 Tải File Excel (CSV)", df.to_csv(index=False).encode('utf-8-sig'), f"Thumb_{domain}.csv", "text/csv")
                
                with tab_copy:
                    st.info("💡 Hướng dẫn: Rê chuột vào góc trên cùng bên phải của khung đen bên dưới, bấm vào biểu tượng Copy 📋. Sau đó mở Excel/Sheet và bấm Ctrl+V.")
                    # Tạo chuỗi Tab-Separated Values (TSV) để copy dán chuẩn cột
                    copy_string = "ID\tLink SP\tLink Ảnh\tTrạng Thái\n"
                    for r in results:
                        copy_string += f"{r['ID']}\t{r['Link SP']}\t{r['Link Ảnh']}\t{r['Trạng Thái']}\n"
                    
                    # Dùng st.code để tạo ra cái khung đen có sẵn nút Copy xịn sò của Streamlit
                    st.code(copy_string, language="text")

# --- TOOL LỌC FILE SHEET ---
elif "4. Lọc File" in menu:
    st.title("📊 Quản Lý & Lọc File (Google Sheet)")
    st.markdown("Kết nối trực tiếp với Sheet hệ thống. Dễ dàng tìm kiếm và xem tiến độ.")
    
    SHEET_ID = "1wtIhG3O1_oDrJcUvgwxcjxeRnrWpqbWIN15c4a37kl0"
    CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=0"
    
    with st.spinner("⏳ Đang tải dữ liệu từ Google Sheet..."):
        try:
            df = pd.read_csv(CSV_URL)
            df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors="coerce")
            
            # Lấy cột "Người Làm" (Giả định cột cuối hoặc cột 28)
            creator_col = df.columns[28] if len(df.columns) > 28 else df.columns[-1]
            
            st.markdown("### 🔍 Bộ Lọc")
            c1, c2 = st.columns(2)
            with c1: 
                creator_list = ["Tất cả"] + df[creator_col].dropna().astype(str).unique().tolist()
                creator_filter = st.selectbox("👨‍💻 Lọc theo người làm:", creator_list)
            with c2: 
                search_kw = st.text_input("🔎 Tìm kiếm Tên Sản Phẩm:")
            
            # Áp dụng bộ lọc
            if creator_filter != "Tất cả": 
                df = df[df[creator_col].astype(str) == creator_filter]
            if search_kw: 
                df = df[df.iloc[:, 3].astype(str).str.lower().str.contains(search_kw.lower())]
            
            # Thống kê nhanh
            col_met1, col_met2 = st.columns(2)
            col_met1.metric("Tổng số dòng hiển thị", len(df))
            
            st.markdown("### 📋 Dữ liệu")
            st.dataframe(df, use_container_width=True, height=500)
            
        except Exception as e: 
            st.error(f"❌ Lỗi tải Sheet: {e}. Vui lòng kiểm tra quyền truy cập công khai của Google Sheet.")
