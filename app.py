import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
import io
import zipfile
import json
import os
from PIL import Image
from urllib.parse import urljoin, urlparse

# ==========================================
# CẤU HÌNH GIAO DIỆN & TÀI KHOẢN
# ==========================================
st.set_page_config(page_title="Hệ Thống Tool ĐỨC", page_icon="🚀", layout="wide")

USERS = {"ducadmin": "matkhau123", "nhanvien1": "123456"}
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
KEYWORD_FILE = "keywords.json"

# ==========================================
# HỆ THỐNG ĐĂNG NHẬP
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center; color: #1A237E;'>🔐 ĐĂNG NHẬP HỆ THỐNG</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập")
            password = st.text_input("Mật khẩu", type="password")
            if st.form_submit_button("🚀 Đăng nhập", use_container_width=True):
                if username in USERS and USERS[username] == password:
                    st.session_state["logged_in"] = True
                    st.session_state["user"] = username
                    st.rerun()
                else:
                    st.error("❌ Sai tên đăng nhập hoặc mật khẩu!")
    st.stop()

# ==========================================
# MENU SIDEBAR
# ==========================================
st.sidebar.markdown(f"### 👋 Xin chào, **{st.session_state['user'].upper()}**!")
st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "📌 CHỌN CÔNG CỤ",
    [
        "🏠 0. Trang chủ", 
        "🔗 1. Công Cụ Chèn Link (JSON)",
        "🔍 2. Lấy ID & Tên Sản Phẩm", 
        "🏪 3. Check Trạng Thái DMX", 
        "📸 4. Lấy Thumb DMX", 
        "📸 5. Lấy Thumb TGDD",
        "📊 6. Lọc File (Google Sheet)",
        "✂️ 7. Resize Ảnh Hàng Loạt",
        "🖼️ 8. Tải Hình Gallery (Chọn Màu)"
    ]
)
st.sidebar.markdown("---")
if st.sidebar.button("🚪 Đăng xuất", use_container_width=True):
    st.session_state["logged_in"] = False
    st.rerun()

# ==========================================
# CÁC HÀM TIỆN ÍCH DÙNG CHUNG
# ==========================================
def load_keywords():
    if os.path.exists(KEYWORD_FILE):
        try:
            with open(KEYWORD_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except: pass
    return {"Thế Giới Di Động": {}, "Điện Máy Xanh": {}, "TopZone": {}}

def save_keywords(data):
    with open(KEYWORD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fetch_thumb(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        m = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', r.text, re.I)
        return m.group(1) if m else "Không tìm thấy"
    except:
        return "Lỗi kết nối"

def clean_name(name):
    cleaned = re.sub(r'[\\/:*?"<>|]', "", name)
    return re.sub(r"\s+", " ", cleaned).strip()

# ==========================================
# TOOL 0: TRANG CHỦ
# ==========================================
if "0. Trang chủ" in menu:
    st.title("🌟 BẢNG ĐIỀU KHIỂN TRUNG TÂM")
    st.info("Phiên bản Web PRO - Tích hợp đầy đủ 8 Tool. Hệ thống JSON và ZIP file đã được kích hoạt.")

# ==========================================
# TOOL 1: CHÈN LINK (CÓ JSON)
# ==========================================
elif "1. Công Cụ Chèn Link" in menu:
    st.title("🔗 Tool Quản Lý Từ Khóa & Chèn Link")
    kw_data = load_keywords()
    
    tab1, tab2 = st.tabs(["✍️ Chèn Link Vào Bài", "⚙️ Quản Lý Từ Khóa (JSON)"])
    
    with tab2:
        st.subheader("Thêm từ khóa mới")
        c1, c2, c3 = st.columns(3)
        with c1: site_sel = st.selectbox("Chọn trang", ["Thế Giới Di Động", "Điện Máy Xanh", "TopZone"])
        with c2: new_kw = st.text_input("Từ khóa")
        with c3: new_link = st.text_input("Link chèn")
        if st.button("➕ Thêm vào Database"):
            if new_kw and new_link:
                kw_data[site_sel][new_kw] = new_link
                save_keywords(kw_data)
                st.success("Đã lưu vào JSON!")
                st.rerun()
                
        st.subheader(f"Danh sách từ khóa: {site_sel}")
        st.json(kw_data[site_sel])
        
    with tab1:
        site_use = st.selectbox("Dùng bộ từ khóa của trang:", ["Thế Giới Di Động", "Điện Máy Xanh", "TopZone"])
        raw_text = st.text_area("Dán nội dung bài viết:", height=200)
        if st.button("🚀 Xử lý chèn link", type="primary"):
            if not raw_text: st.warning("Chưa nhập text!")
            else:
                result_text = raw_text
                for kw, link in kw_data[site_use].items():
                    # Thay thế từ khóa bằng thẻ <a> HTML
                    pattern = re.compile(rf'(?i)\b({re.escape(kw)})\b')
                    result_text = pattern.sub(f'<a href="{link}" target="_blank">\\1</a>', result_text)
                st.subheader("Kết quả (HTML):")
                st.code(result_text, language="html")
                st.subheader("Hiển thị thử:")
                st.markdown(result_text, unsafe_allow_html=True)

# ==========================================
# TOOL 2: LẤY ID SP
# ==========================================
elif "2. Lấy ID" in menu:
    st.title("🔍 Tool Quét Tên & ID Sản Phẩm")
    raw_input = st.text_area("Dán Link (Mỗi link 1 dòng):", height=150)
    if st.button("🚀 Quét dữ liệu"):
        links = [l.strip() for l in raw_input.splitlines() if l.strip()]
        results = []
        bar = st.progress(0)
        for i, link in enumerate(links):
            try:
                soup = BeautifulSoup(requests.get(link, headers=HEADERS, timeout=10).text, "html.parser")
                name = soup.select_one("div.product-name h1")
                img = soup.select_one("img[src*='/Products/Images/']")
                p_id = re.search(r"Images/\d+/(\d+)/", img.get("src", "")).group(1) if img else "Không tìm thấy"
                results.append({"Tên SP": name.text.strip() if name else "Lỗi", "ID": p_id, "Link": link})
            except:
                results.append({"Tên SP": "Lỗi", "ID": "Lỗi", "Link": link})
            bar.progress((i + 1) / len(links))
        
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Tải Excel", df.to_csv(index=False).encode('utf-8-sig'), "ID_SP.csv", "text/csv")

# ==========================================
# TOOL 3: CHECK TRẠNG THÁI DMX
# ==========================================
elif "3. Check Trạng Thái DMX" in menu:
    st.title("🏪 Tool Check Trạng Thái DMX")
    raw_input = st.text_area("Dán ID (Mỗi ID 1 dòng):", height=150)
    if st.button("🚀 Kiểm tra"):
        ids = [l.strip() for l in raw_input.splitlines() if l.strip()]
        results, bar = [], st.progress(0)
        for i, pid in enumerate(ids):
            pid_num = re.search(r'(\d+)', pid).group(1) if re.search(r'(\d+)', pid) else pid
            try:
                soup = BeautifulSoup(requests.get(f"https://www.dienmayxanh.com/sp-{pid_num}", headers=HEADERS, timeout=10).text, 'html.parser')
                name_tag = soup.find('h1')
                status_tag = soup.find('strong', class_='productstatus orange')
                status = "Hết hàng tạm thời" if status_tag and "Hết hàng" in status_tag.text else "Đang kinh doanh" if soup.find('p', class_='box-price-present') else "Không xác định"
                results.append({"ID": pid_num, "Tên SP": name_tag.text.strip() if name_tag else "Lỗi", "Trạng Thái": status})
            except:
                results.append({"ID": pid_num, "Tên SP": "Lỗi", "Trạng Thái": "Lỗi"})
            bar.progress((i + 1) / len(ids))
            
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Tải Excel", df.to_csv(index=False).encode('utf-8-sig'), "Status_DMX.csv", "text/csv")

# ==========================================
# TOOL 4 & 5: LẤY THUMB DMX / TGDD
# ==========================================
elif "Lấy Thumb" in menu:
    domain = "dienmayxanh.com" if "DMX" in menu else "thegioididong.com"
    st.title(f"📸 Tool Quét Link Ảnh Thumbnail ({domain})")
    raw_input = st.text_area("Dán ID (Mỗi ID 1 dòng):", height=150)
    if st.button("🚀 Quét Ảnh"):
        ids = [l.strip() for l in raw_input.splitlines() if l.strip()]
        results, bar = [], st.progress(0)
        for i, pid in enumerate(ids):
            url = f"https://www.{domain}/sp-{pid}"
            results.append({"ID": pid, "Link SP": url, "Link Ảnh": fetch_thumb(url)})
            bar.progress((i + 1) / len(ids))
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Tải Excel", df.to_csv(index=False).encode('utf-8-sig'), f"Thumb_{domain}.csv", "text/csv")

# ==========================================
# TOOL 6: LỌC FILE SHEET
# ==========================================
elif "6. Lọc File" in menu:
    st.title("📊 Tool Lọc & Quản Lý File (Từ Google Sheet)")
    SHEET_ID = "1wtIhG3O1_oDrJcUvgwxcjxeRnrWpqbWIN15c4a37kl0"
    CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=0"
    
    try:
        df = pd.read_csv(CSV_URL)
        df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors="coerce")
        creator_col = df.columns[28] if len(df.columns) > 28 else df.columns[-1]
        
        c1, c2 = st.columns(2)
        with c1: creator_filter = st.selectbox("Lọc theo người làm:", ["Tất cả"] + df[creator_col].dropna().astype(str).unique().tolist())
        with c2: search_kw = st.text_input("Tìm Tên SP:")
        
        if creator_filter != "Tất cả": df = df[df[creator_col].astype(str) == creator_filter]
        if search_kw: df = df[df.iloc[:, 3].astype(str).str.lower().str.contains(search_kw.lower())]
        
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Lỗi tải Sheet: {e}. Vui lòng kiểm tra quyền truy cập link Google Sheet.")

# ==========================================
# TOOL 7: RESIZE ẢNH
# ==========================================
elif "7. Resize Ảnh" in menu:
    st.title("✂️ Cắt / Resize Ảnh Hàng Loạt Chuẩn Kích Thước")
    size_option = st.selectbox("Chọn kích thước:", ["1020x680", "1020x570", "1200x1200"])
    uploaded_files = st.file_uploader("Kéo thả nhiều ảnh vào đây", accept_multiple_files=True, type=['jpg', 'jpeg', 'png', 'webp'])
    
    if uploaded_files and st.button("🚀 Bắt đầu Resize"):
        w, h = map(int, size_option.split("x"))
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            bar = st.progress(0)
            for i, file in enumerate(uploaded_files):
                try:
                    img = Image.open(file).convert("RGBA")
                    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
                    bg.paste(img, (0, 0), img)
                    img = bg.convert("RGB")
                    
                    img_ratio, target_ratio = img.width / img.height, w / h
                    new_w, new_h = (w, int(w / img_ratio)) if img_ratio > target_ratio else (int(h * img_ratio), h)
                    
                    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    new_img = Image.new("RGB", (w, h), (255, 255, 255))
                    new_img.paste(resized, ((w - new_w) // 2, (h - new_h) // 2))

                    img_byte_arr = io.BytesIO()
                    new_img.save(img_byte_arr, format='JPEG', quality=95)
                    zip_file.writestr(file.name.rsplit('.', 1)[0] + ".jpg", img_byte_arr.getvalue())
                except: pass
                bar.progress((i + 1) / len(uploaded_files))
                
        st.success("✅ Xử lý hoàn tất!")
        st.download_button("📦 Tải File ZIP Ảnh", zip_buffer.getvalue(), "Anh_Da_Resize.zip", "application/zip")

# ==========================================
# TOOL 8: TẢI HÌNH GALLERY
# ==========================================
elif "8. Tải Hình Gallery" in menu:
    st.title("🖼️ Tải Hình Gallery Mọi Phiên Bản Màu")
    url_input = st.text_input("Dán link SP cần tải (Ví dụ: https://www.thegioididong.com/...)")
    
    if "colors_data" not in st.session_state: st.session_state.colors_data = []
    
    if st.button("🔍 Quét Các Màu"):
        try:
            soup = BeautifulSoup(requests.get(url_input, headers=HEADERS, timeout=10).text, "html.parser")
            parsed = urlparse(url_input)
            st.session_state.colors_data = [{"name": a.get_text(strip=True), "link": urljoin(url_input, a["href"])} for a in soup.find_all("a", href=True) if parsed.path in a["href"] and "?code=" in a["href"]]
            if not st.session_state.colors_data: st.session_state.colors_data = [{"name": "Mặc định", "link": url_input}]
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi: {e}")
            
    if st.session_state.colors_data:
        st.markdown("### Chọn màu muốn tải:")
        selected_colors = []
        for color in st.session_state.colors_data:
            if st.checkbox(color["name"], value=True): selected_colors.append(color)
            
        if st.button("📥 Bắt đầu Tải & Đóng Gói (ZIP)", type="primary"):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for color in selected_colors:
                    try:
                        c_soup = BeautifulSoup(requests.get(color["link"], headers=HEADERS, timeout=10).text, "html.parser")
                        img_urls = [urljoin(color["link"], img.get("data-src") or img.get("src")) for img in c_soup.find_all("img") if (img.get("data-src") or img.get("src")) and "750x500" in (img.get("data-src") or img.get("src"))]
                        
                        for img_url in img_urls:
                            clean_url = re.sub(r"-750x500", "", img_url)
                            file_name = f"{clean_name(color['name'])}/{os.path.basename(clean_url.split('?')[0])}"
                            img_data = requests.get(clean_url, headers=HEADERS).content
                            zip_file.writestr(file_name, img_data)
                    except: pass
            
            st.success("✅ Đã gom xong toàn bộ ảnh vào File ZIP!")
            st.download_button("📦 Bấm Tải Xuống File ZIP", zip_buffer.getvalue(), "Gallery_Images.zip", "application/zip")
