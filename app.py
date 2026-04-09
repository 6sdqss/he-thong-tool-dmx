import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
import json
import os
import io
import zipfile
from requests.utils import cookiejar_from_dict
from PIL import Image

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

# Khởi tạo Két sắt bộ nhớ 
if "thumb_results" not in st.session_state:
    st.session_state.thumb_results = []
if "thumb_zip" not in st.session_state:
    st.session_state.thumb_zip = None
if "success_count" not in st.session_state:
    st.session_state.success_count = 0

# ==========================================
# KHU VỰC 1: HỆ THỐNG ĐỌC COOKIE TỰ ĐỘNG
# ==========================================
def get_session():
    session = requests.Session()
    session.headers.update(HEADERS)
    
    all_cookies = {}
    if os.path.exists("cookies_dmx.json"):
        try:
            with open("cookies_dmx.json", "r", encoding="utf-8") as f:
                for c in json.load(f):
                    if c.get("name") and c.get("value"): 
                        all_cookies[c.get("name")] = c.get("value")
        except Exception as e: pass
            
    if os.path.exists("cookies_tgdd.json"):
        try:
            with open("cookies_tgdd.json", "r", encoding="utf-8") as f:
                for c in json.load(f):
                    if c.get("name") and c.get("value"): 
                        all_cookies[c.get("name")] = c.get("value")
        except Exception as e: pass
            
    session.cookies = cookiejar_from_dict(all_cookies)
    return session

# ==========================================
# KHU VỰC 2: CÁC HÀM XỬ LÝ LẤY ẢNH 
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

def clean_image_url(url, domain):
    if not url: return url
    
    # BỘ LỌC REGEX THÔNG MINH CHỐNG LỖI XÓA -600x600
    def check_size(match):
        w, h = int(match.group(1)), int(match.group(2))
        # Chỉ xóa nếu kích thước nhỏ hơn 600x600 hoặc chuẩn 750x500
        if (w < 600 and h < 600) or (w == 750 and h == 500):
            return ""
        return match.group(0) # Giữ nguyên các số >= 600x600
        
    cleaned = re.sub(r'-(\d+)x(\d+)(?=\.(?:jpg|jpeg|png|webp))', check_size, url, flags=re.IGNORECASE)
    
    if cleaned.startswith("//"): return "https:" + cleaned
    elif cleaned.startswith("/"): 
        cdn_prefix = "cdn.dienmayxanh.com" if "dienmayxanh" in domain else "cdnv2.tgdd.vn"
        return f"https://{cdn_prefix}" + cleaned
    elif not cleaned.startswith("http"): return "https://" + cleaned
    return cleaned

def fetch_by_page(session, product_id, domain):
    short_url = f"https://www.{domain}/sp-{product_id}"
    try:
        r = session.get(short_url, headers=HEADERS, allow_redirects=True, timeout=12)
        if r.status_code != 200: return None, None, f"HTTP {r.status_code}"
        html = r.text
        m = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', html, re.I)
        if m: return r.url, m.group(1), "OK(Page-og)"
        m2 = re.search(r'(https?://[^"\']+(?:cdnv2.tgdd.vn|cdn.tgdd.vn|cdnv2.tgdd|tgdd.vn|cdn.dienmayxanh.com)[^"\']+\.(?:png|jpg|jpeg))', html, re.I)
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

if st.session_state["user"] == "ducadmin":
    menu_options = ["🏠 1. Trang chủ", "📸 2. Lấy Thumb DMX", "📸 3. Lấy Thumb TGDD", "📊 4. Lọc File (Google Sheet)"]
else:
    menu_options = ["🏠 1. Trang chủ", "📸 2. Lấy Thumb DMX", "📸 3. Lấy Thumb TGDD"]

menu = st.sidebar.radio("📌 TÍNH NĂNG CHÍNH", menu_options)

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Đăng xuất", use_container_width=True):
    st.session_state["logged_in"] = False
    st.session_state.thumb_results = []
    st.session_state.thumb_zip = None
    st.session_state.success_count = 0
    st.rerun()

if "current_menu" not in st.session_state:
    st.session_state.current_menu = menu
elif st.session_state.current_menu != menu:
    st.session_state.thumb_results = []
    st.session_state.thumb_zip = None
    st.session_state.success_count = 0
    st.session_state.current_menu = menu

# ==========================================
# KHU VỰC 4: GIAO DIỆN CHÍNH
# ==========================================

if "1. Trang chủ" in menu:
    st.title("🌟 TỔNG QUAN HỆ THỐNG")
    st.info("Mẹo: Để trình duyệt hỏi vị trí lưu file ZIP, hãy vào Cài đặt Chrome -> Tệp đã tải xuống -> Bật 'Hỏi vị trí lưu từng tệp trước khi tải xuống'.")

elif "Lấy Thumb" in menu:
    domain = "dienmayxanh.com" if "DMX" in menu else "thegioididong.com"
    logo_color = "#0088FF" if "DMX" in menu else "#FFCA28"
    
    st.markdown(f"<h2 style='color: {logo_color};'>📸 Tool Quét & Ốp Khung Thumbnail ({domain.upper()})</h2>", unsafe_allow_html=True)
    
    uploaded_logo = st.file_uploader("📂 BƯỚC 1: Tải lên Khung/Logo PNG (Nền trong suốt, cùng Tỷ lệ 1:1)", type=['png'])
    if uploaded_logo:
        st.success("✅ Đã nhận File Khung. Hệ thống sẽ ốp đè Khung vừa khít vào ảnh sản phẩm tải về.")

    col1, col2 = st.columns([1, 2.5])
    
    with col1:
        raw_input = st.text_area("✍️ BƯỚC 2: Dán danh sách ID vào đây:", height=300)
        btn_run = st.button("🚀 QUÉT VÀ XỬ LÝ ẢNH", type="primary", use_container_width=True)

    with col2:
        if btn_run:
            if not raw_input.strip():
                st.warning("⚠️ Vui lòng nhập ít nhất 1 ID!")
            else:
                ids = [l.strip() for l in raw_input.splitlines() if l.strip()]
                temp_results = []
                zip_buffer = io.BytesIO()
                success_count = 0
                
                logo_img = None
                if uploaded_logo:
                    logo_img = Image.open(uploaded_logo).convert("RGBA")
                
                progress_text = st.empty()
                progress_bar = st.progress(0)
                session = get_session()
                
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
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
                            status = "OK" if thumb else "Lỗi API"
                            
                        thumb_clean = clean_image_url(thumb, domain) if thumb else ""
                        if not final_url: final_url = f"https://www.{domain}/sp-{pid_num}"
                        
                        dl_status = ""
                        if thumb_clean:
                            try:
                                img_resp = session.get(thumb_clean, timeout=15)
                                if img_resp.status_code == 200:
                                    base_img = Image.open(io.BytesIO(img_resp.content)).convert("RGBA")
                                    
                                    if logo_img:
                                        logo_resized = logo_img.resize(base_img.size, Image.Resampling.LANCZOS)
                                        base_img.paste(logo_resized, (0, 0), mask=logo_resized)
                                    
                                    out_img_bytes = io.BytesIO()
                                    base_img.convert("RGB").save(out_img_bytes, format="JPEG", quality=95)
                                    zip_file.writestr(f"{pid_num}.jpg", out_img_bytes.getvalue())
                                    
                                    dl_status = " [Đã tải & Xử lý]"
                                    success_count += 1
                                else:
                                    dl_status = f" [Lỗi tải HTTP {img_resp.status_code}]"
                            except Exception as e:
                                dl_status = f" [Lỗi tải ảnh]"

                        out_status = ("OK" if thumb_clean else "Không có ảnh") + dl_status
                        
                        temp_results.append({
                            "ID": pid_num, 
                            "Link SP": final_url, 
                            "Link Ảnh": thumb_clean, 
                            "Trạng Thái": out_status
                        })
                        
                        progress_bar.progress((i + 1) / len(ids))
                        time.sleep(0.12)
                
                progress_text.success(f"✅ QUÉT HOÀN TẤT! Thành công {success_count}/{len(ids)} ảnh.")
                
                # CẬP NHẬT KÉT SẮT
                st.session_state.thumb_results = temp_results
                st.session_state.thumb_zip = zip_buffer.getvalue()
                st.session_state.success_count = success_count

        # HIỂN THỊ KẾT QUẢ 
        if st.session_state.thumb_results:
            if st.session_state.success_count > 0:
                st.download_button(
                    label=f"📦 TẢI BỘ {st.session_state.success_count} ẢNH VỀ MÁY (FILE ZIP)", 
                    data=st.session_state.thumb_zip, 
                    file_name=f"Anh_San_Pham_{domain}.zip", 
                    mime="application/zip",
                    type="primary"
                )
            else:
                st.error("❌ Cảnh báo: Không có ảnh nào tải thành công. Vui lòng kiểm tra lại cột Trạng Thái bên dưới xem lỗi do đâu (bị chặn cookie hoặc sai ID)!")

            df = pd.DataFrame(st.session_state.thumb_results)
            tab_table, tab_copy = st.tabs(["📋 Bảng dữ liệu Link", "📝 Nút Copy Nhanh (Dán Excel)"])
            
            with tab_table:
                st.dataframe(df, use_container_width=True)
            
            with tab_copy:
                copy_string = "ID\tLink SP\tLink Ảnh\tTrạng Thái\n"
                for r in st.session_state.thumb_results:
                    copy_string += f"{r['ID']}\t{r['Link SP']}\t{r['Link Ảnh']}\t{r['Trạng Thái']}\n"
                st.code(copy_string, language="text")

elif "4. Lọc File" in menu:
    st.title("📊 Quản Lý & Lọc File (Google Sheet)")
    st.markdown("Kết nối trực tiếp với Sheet hệ thống. Dễ dàng tìm kiếm và xem tiến độ.")
    
    SHEET_ID = "1wtIhG3O1_oDrJcUvgwxcjxeRnrWpqbWIN15c4a37kl0"
    CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=0"
    
    with st.spinner("⏳ Đang tải dữ liệu từ Google Sheet..."):
        try:
            df = pd.read_csv(CSV_URL)
            df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors="coerce")
            
            creator_col = df.columns[28] if len(df.columns) > 28 else df.columns[-1]
            
            st.markdown("### 🔍 Bộ Lọc")
            c1, c2 = st.columns(2)
            with c1: 
                creator_list = ["Tất cả"] + df[creator_col].dropna().astype(str).unique().tolist()
                creator_filter = st.selectbox("👨‍💻 Lọc theo người làm:", creator_list)
            with c2: 
                search_kw = st.text_input("🔎 Tìm kiếm Tên Sản Phẩm:")
            
            if creator_filter != "Tất cả": 
                df = df[df[creator_col].astype(str) == creator_filter]
            if search_kw: 
                df = df[df.iloc[:, 3].astype(str).str.lower().str.contains(search_kw.lower())]
            
            col_met1, col_met2 = st.columns(2)
            col_met1.metric("Tổng số dòng hiển thị", len(df))
            
            st.markdown("### 📋 Dữ liệu")
            st.dataframe(df, use_container_width=True, height=500)
            
        except Exception as e: 
            st.error(f"❌ Lỗi tải Sheet: {e}. Vui lòng kiểm tra quyền truy cập công khai của Google Sheet.")
