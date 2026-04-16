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
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import hashlib
import base64
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================================
# CẤU HÌNH TRANG
# ==========================================
st.set_page_config(
    page_title="ĐỨC CONTENT PRO", 
    page_icon="💎", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CSS TOÀN CỤC - GIAO DIỆN XỊN XÒ
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600&display=swap');

/* ===== RESET & BASE ===== */
*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Be Vietnam Pro', sans-serif !important;
}

/* ===== NỀN GRADIENT ĐỘNG ===== */
.stApp {
    background: linear-gradient(135deg, #0a0e1a 0%, #0d1526 40%, #0a1628 70%, #0f172a 100%);
    min-height: 100vh;
}

.stApp::before {
    content: '';
    position: fixed;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: 
        radial-gradient(ellipse at 20% 20%, rgba(0, 123, 255, 0.06) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 80%, rgba(99, 102, 241, 0.05) 0%, transparent 50%),
        radial-gradient(ellipse at 50% 50%, rgba(6, 182, 212, 0.03) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
}

/* ===== SIDEBAR ===== */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1526 0%, #0a1120 100%) !important;
    border-right: 1px solid rgba(0, 123, 255, 0.15) !important;
}

[data-testid="stSidebar"] .stRadio label {
    color: #94a3b8 !important;
    font-weight: 500 !important;
    padding: 8px 12px !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
    display: block !important;
    margin: 2px 0 !important;
}

[data-testid="stSidebar"] .stRadio label:hover {
    color: #e2e8f0 !important;
    background: rgba(0, 123, 255, 0.1) !important;
}

/* ===== TEXT COLORS ===== */
h1, h2, h3 { color: #e2e8f0 !important; }
p, li, span { color: #94a3b8; }
label { color: #94a3b8 !important; }
.stMarkdown p { color: #94a3b8; }

/* ===== INPUTS ===== */
.stTextInput input, .stTextArea textarea, .stSelectbox select {
    background: rgba(15, 23, 42, 0.8) !important;
    border: 1px solid rgba(0, 123, 255, 0.25) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-family: 'Be Vietnam Pro', sans-serif !important;
    transition: border-color 0.2s ease !important;
}

.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: rgba(0, 123, 255, 0.6) !important;
    box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1) !important;
}

/* ===== BUTTONS ===== */
.stButton > button {
    background: linear-gradient(135deg, #0057e7 0%, #0041b5 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-family: 'Be Vietnam Pro', sans-serif !important;
    letter-spacing: 0.3px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 15px rgba(0, 87, 231, 0.3) !important;
}

.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(0, 87, 231, 0.45) !important;
}

.stButton > button:active { transform: translateY(0) !important; }

/* ===== DOWNLOAD BUTTON ===== */
.stDownloadButton > button {
    background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    box-shadow: 0 4px 15px rgba(5, 150, 105, 0.3) !important;
}

.stDownloadButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(5, 150, 105, 0.45) !important;
}

/* ===== ALERTS ===== */
.stSuccess {
    background: rgba(5, 150, 105, 0.12) !important;
    border: 1px solid rgba(5, 150, 105, 0.3) !important;
    border-radius: 10px !important;
    color: #6ee7b7 !important;
}

.stWarning {
    background: rgba(245, 158, 11, 0.12) !important;
    border: 1px solid rgba(245, 158, 11, 0.3) !important;
    border-radius: 10px !important;
    color: #fcd34d !important;
}

.stError {
    background: rgba(239, 68, 68, 0.12) !important;
    border: 1px solid rgba(239, 68, 68, 0.3) !important;
    border-radius: 10px !important;
    color: #fca5a5 !important;
}

.stInfo {
    background: rgba(0, 123, 255, 0.1) !important;
    border: 1px solid rgba(0, 123, 255, 0.25) !important;
    border-radius: 10px !important;
    color: #93c5fd !important;
}

/* ===== DATAFRAME ===== */
.stDataFrame {
    border: 1px solid rgba(0, 123, 255, 0.15) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* ===== TABS ===== */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(15, 23, 42, 0.6) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
}

.stTabs [data-baseweb="tab"] {
    color: #64748b !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}

.stTabs [aria-selected="true"] {
    background: rgba(0, 87, 231, 0.2) !important;
    color: #60a5fa !important;
}

/* ===== PROGRESS BAR ===== */
.stProgress > div > div {
    background: linear-gradient(90deg, #0057e7, #06b6d4) !important;
    border-radius: 9999px !important;
}

/* ===== FILE UPLOADER ===== */
[data-testid="stFileUploader"] {
    background: rgba(15, 23, 42, 0.6) !important;
    border: 2px dashed rgba(0, 123, 255, 0.25) !important;
    border-radius: 12px !important;
    transition: border-color 0.2s ease !important;
}

[data-testid="stFileUploader"]:hover {
    border-color: rgba(0, 123, 255, 0.5) !important;
}

/* ===== METRICS ===== */
[data-testid="metric-container"] {
    background: rgba(15, 23, 42, 0.7) !important;
    border: 1px solid rgba(0, 123, 255, 0.15) !important;
    border-radius: 12px !important;
    padding: 16px !important;
}

[data-testid="stMetricValue"] { color: #60a5fa !important; font-weight: 800 !important; }
[data-testid="stMetricLabel"] { color: #64748b !important; }

/* ===== CODE BLOCK ===== */
.stCode, code {
    background: rgba(10, 14, 26, 0.9) !important;
    border: 1px solid rgba(0, 123, 255, 0.15) !important;
    border-radius: 10px !important;
    font-family: 'JetBrains Mono', monospace !important;
    color: #a5f3fc !important;
}

/* ===== SPINNER ===== */
.stSpinner > div { border-top-color: #0057e7 !important; }

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: rgba(15, 23, 42, 0.5); }
::-webkit-scrollbar-thumb { background: rgba(0, 87, 231, 0.4); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0, 87, 231, 0.7); }

/* ===== CUSTOM CARDS ===== */
.pro-card {
    background: rgba(13, 21, 38, 0.8);
    border: 1px solid rgba(0, 123, 255, 0.15);
    border-radius: 16px;
    padding: 20px 24px;
    margin: 8px 0;
    backdrop-filter: blur(10px);
    position: relative;
    overflow: hidden;
}

.pro-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(0, 87, 231, 0.6), transparent);
}

.stat-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.3px;
}

.badge-success { background: rgba(5, 150, 105, 0.15); color: #6ee7b7; border: 1px solid rgba(5,150,105,0.3); }
.badge-info { background: rgba(0, 87, 231, 0.15); color: #93c5fd; border: 1px solid rgba(0,87,231,0.3); }
.badge-warn { background: rgba(245, 158, 11, 0.15); color: #fcd34d; border: 1px solid rgba(245,158,11,0.3); }
.badge-error { background: rgba(239, 68, 68, 0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); }

.page-title {
    font-size: 28px;
    font-weight: 900;
    letter-spacing: -0.5px;
    margin-bottom: 4px;
}

.page-subtitle {
    font-size: 14px;
    color: #475569;
    margin-bottom: 24px;
}

.step-label {
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #0057e7;
    margin-bottom: 4px;
}

.divider {
    height: 1px;
    background: linear-gradient(90deg, rgba(0,87,231,0.3), transparent);
    margin: 20px 0;
}

.result-img-wrapper {
    background: rgba(13, 21, 38, 0.9);
    border: 1px solid rgba(0,123,255,0.2);
    border-radius: 10px;
    padding: 8px;
    display: inline-block;
}

.watermark-option {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    border-radius: 8px;
    background: rgba(0,87,231,0.08);
    border: 1px solid rgba(0,87,231,0.2);
    margin: 4px 0;
    font-size: 13px;
    color: #94a3b8;
}

/* ===== LOGIN PAGE ===== */
.login-container {
    max-width: 440px;
    margin: 0 auto;
}

.login-logo {
    text-align: center;
    padding: 32px 0 8px;
}

.login-logo .gem { font-size: 52px; filter: drop-shadow(0 0 20px rgba(0,87,231,0.6)); }

.login-title {
    font-size: 26px;
    font-weight: 900;
    text-align: center;
    background: linear-gradient(135deg, #60a5fa 0%, #06b6d4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 4px;
}

.login-subtitle {
    text-align: center;
    color: #475569;
    font-size: 13px;
    margin-bottom: 28px;
}

/* Image grid preview */
.img-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 10px;
    margin-top: 12px;
}

.img-cell {
    aspect-ratio: 1;
    border-radius: 8px;
    overflow: hidden;
    background: rgba(15,23,42,0.8);
    border: 1px solid rgba(0,123,255,0.15);
    position: relative;
}

.img-cell img { width: 100%; height: 100%; object-fit: cover; }

.img-cell-label {
    position: absolute;
    bottom: 0; left: 0; right: 0;
    background: linear-gradient(transparent, rgba(0,0,0,0.8));
    color: white;
    font-size: 10px;
    padding: 12px 6px 4px;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# CONSTANTS
# ==========================================
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}
USER_FILE = "users.json"

# ==========================================
# USER MANAGEMENT
# ==========================================
def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def load_users():
    base_users = {
        "ducpro": hash_password("234766"),
        "tuanpro": hash_password("174900"),
        "guest": hash_password("234766")
    }
    if os.path.exists(USER_FILE):
        try:
            with open(USER_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            # Nâng cấp user cũ nếu chưa hash
            upgraded = {}
            for k, v in saved.items():
                if len(v) != 64:  # chưa hash
                    upgraded[k] = hash_password(v)
                else:
                    upgraded[k] = v
            for k, v in base_users.items():
                upgraded[k] = v
            return upgraded
        except Exception:
            pass
    save_users(base_users)
    return base_users

def save_users(users_dict):
    try:
        with open(USER_FILE, "w", encoding="utf-8") as f:
            json.dump(users_dict, f, indent=4)
    except Exception as e:
        st.error(f"Lỗi lưu tài khoản: {e}")

def verify_password(users: dict, username: str, password: str) -> bool:
    if username not in users:
        return False
    stored = users[username]
    if len(stored) == 64:
        return stored == hash_password(password)
    return stored == password  # legacy

USERS = load_users()

# ==========================================
# SESSION STATE INIT
# ==========================================
defaults = {
    "logged_in": False,
    "user": "",
    "thumb_results": [],
    "thumb_zip": None,
    "success_count": 0,
    "current_menu": "",
    "preview_images": [],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ==========================================
# NETWORK SESSION
# ==========================================
def get_session():
    session = requests.Session()
    session.headers.update(HEADERS)
    all_cookies = {}
    for fn in ["cookies_dmx.json", "cookies_tgdd.json"]:
        if os.path.exists(fn):
            try:
                with open(fn, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        for c in json.loads(content):
                            if isinstance(c, dict) and c.get("name") and c.get("value"):
                                all_cookies[c.get("name")] = c.get("value")
            except Exception:
                pass
    session.cookies = cookiejar_from_dict(all_cookies)
    return session

# ==========================================
# IMAGE PROCESSING HELPERS
# ==========================================
def extract_simage_thumb(simage_str):
    if not simage_str:
        return None
    try:
        images = json.loads(simage_str)
        if not isinstance(images, list):
            return None
        thumb = None
        for img in images:
            if isinstance(img, dict) and img.get("PictureUrl"):
                if img.get("IsThumb") is True:
                    return img["PictureUrl"]
                if thumb is None:
                    thumb = img["PictureUrl"]
        return thumb
    except Exception:
        if simage_str.startswith(("http", "//", "/")):
            return simage_str
        return None

def clean_image_url(url: str, domain: str) -> str:
    if not url:
        return url

    def check_size(m):
        w, h = int(m.group(1)), int(m.group(2))
        if (w < 600 and h < 600) or (w == 750 and h == 500):
            return ""
        return m.group(0)

    cleaned = re.sub(r'-(\d+)x(\d+)(?=\.(?:jpg|jpeg|png|webp))', check_size, url, flags=re.IGNORECASE)
    if cleaned.startswith("//"):
        return "https:" + cleaned
    elif cleaned.startswith("/"):
        cdn = "cdn.dienmayxanh.com" if "dienmayxanh" in domain else "cdnv2.tgdd.vn"
        return f"https://{cdn}" + cleaned
    elif not cleaned.startswith("http"):
        return "https://" + cleaned
    return cleaned

def fetch_by_page(session, pid, domain):
    short_url = f"https://www.{domain}/sp-{pid}"
    try:
        r = session.get(short_url, headers=HEADERS, allow_redirects=True, timeout=12)
        if r.status_code != 200:
            return None, None, f"HTTP {r.status_code}"
        m = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', r.text, re.I)
        if m:
            return r.url, m.group(1), "OK(Page-og)"
        m2 = re.search(r'(https?://[^"\']+(?:cdnv2\.tgdd\.vn|cdn\.tgdd\.vn|cdn\.dienmayxanh\.com)[^"\']+\.(?:png|jpg|jpeg))', r.text, re.I)
        if m2:
            return r.url, m2.group(1), "OK(Page-find)"
        return r.url, None, "NoImageFound"
    except Exception as e:
        return None, None, f"Error: {e}"

def fetch_by_api(session, pid, domain):
    api_url = f"https://www.{domain}/apiweb/productdetails?productId={pid}"
    try:
        r = session.get(api_url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return None, None, f"API HTTP {r.status_code}"
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
                    if seo:
                        break
        thumb_from_simage = extract_simage_thumb(simage) if simage else None
        if thumb_from_simage:
            pic = thumb_from_simage
        if seo:
            final_url = f"https://www.{domain}" + seo if seo.startswith("/") else seo
            return final_url, pic or "", "OK"
        return None, pic or "", "Lỗi API"
    except Exception as e:
        return None, None, f"API_error: {e}"

def process_image(base_img: Image.Image, logo_img=None, watermark_text="", brightness=1.0, sharpen=False) -> Image.Image:
    """Xử lý ảnh: ghép logo, watermark text, brightness, sharpen"""
    img = base_img.convert("RGBA")

    # Chỉnh sáng
    if brightness != 1.0:
        enhancer = ImageEnhance.Brightness(img.convert("RGB"))
        img = enhancer.enhance(brightness).convert("RGBA")

    # Sharpen
    if sharpen:
        img = img.filter(ImageFilter.SHARPEN)

    # Ghép logo
    if logo_img:
        logo_resized = logo_img.resize(img.size, Image.Resampling.LANCZOS)
        img.paste(logo_resized, (0, 0), mask=logo_resized)

    # Watermark text (góc dưới phải)
    if watermark_text.strip():
        draw = ImageDraw.Draw(img)
        w, h = img.size
        font_size = max(14, int(w * 0.025))
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        margin = int(w * 0.02)
        x, y = w - tw - margin, h - th - margin
        # Shadow
        draw.text((x + 2, y + 2), watermark_text, font=font, fill=(0, 0, 0, 120))
        draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 200))

    return img

def img_to_bytes(img: Image.Image, quality=92) -> bytes:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()

# ==========================================
# LOGIN PAGE
# ==========================================
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.8, 1])
    with col:
        st.markdown("""
        <div class="login-logo"><span class="gem">💎</span></div>
        <div class="login-title">ĐỨC CONTENT PRO</div>
        <div class="login-subtitle">Hệ thống thu thập & xử lý ảnh sản phẩm thương mại điện tử</div>
        """, unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["🔐  Đăng Nhập", "📝  Đăng Ký"])

        with tab_login:
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Tên đăng nhập", placeholder="Nhập tên đăng nhập...")
                password = st.text_input("Mật khẩu", type="password", placeholder="Nhập mật khẩu...")
                submitted = st.form_submit_button("🚀  Đăng nhập", use_container_width=True)
                if submitted:
                    u = username.strip()
                    p = password.strip()
                    if verify_password(USERS, u, p):
                        st.session_state.logged_in = True
                        st.session_state.user = u
                        st.rerun()
                    else:
                        st.error("❌ Tên đăng nhập hoặc mật khẩu không đúng!")

        with tab_register:
            with st.form("register_form", clear_on_submit=True):
                new_user = st.text_input("Tên đăng nhập mới", placeholder="Từ 3 ký tự, không dấu...")
                new_pass = st.text_input("Mật khẩu", type="password", placeholder="Tối thiểu 6 ký tự...")
                new_pass2 = st.text_input("Xác nhận mật khẩu", type="password", placeholder="Nhập lại mật khẩu...")
                reg_btn = st.form_submit_button("✅  Tạo tài khoản", use_container_width=True)
                if reg_btn:
                    u = new_user.strip()
                    p = new_pass.strip()
                    if len(u) < 3:
                        st.warning("⚠️ Tên đăng nhập phải có ít nhất 3 ký tự!")
                    elif len(p) < 6:
                        st.warning("⚠️ Mật khẩu phải có ít nhất 6 ký tự!")
                    elif u in USERS:
                        st.error("❌ Tên này đã tồn tại!")
                    elif p != new_pass2.strip():
                        st.error("❌ Mật khẩu xác nhận không khớp!")
                    else:
                        USERS[u] = hash_password(p)
                        save_users(USERS)
                        st.success("✅ Tạo tài khoản thành công! Hãy đăng nhập.")
    st.stop()

# ==========================================
# SIDEBAR
# ==========================================
current_user = st.session_state.user
is_admin = current_user == "ducpro"

with st.sidebar:
    st.markdown(f"""
    <div style="padding: 12px 0 16px;">
        <div style="font-size:13px; color:#475569; font-weight:600; letter-spacing:1px; text-transform:uppercase; margin-bottom:6px;">Đăng nhập với</div>
        <div style="font-size:18px; font-weight:800; color:#60a5fa;">👤 {current_user.upper()}</div>
        {'<span class="stat-badge badge-info" style="font-size:11px; margin-top:4px;">⚡ Admin</span>' if is_admin else ''}
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    menu_options = [
        "🏠  Trang Chủ",
        "📸  Thu Ảnh — DienmayXanh",
        "📸  Thu Ảnh — Thegioididong",
        "🔗  Thu Ảnh — Link Trực Tiếp",
    ]
    if is_admin:
        menu_options.append("📊  Quản Lý Google Sheet")
        menu_options.append("👥  Quản Lý Tài Khoản")

    menu = st.radio("MENU CHÍNH", menu_options, label_visibility="visible")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Stats session
    if st.session_state.success_count > 0:
        st.markdown(f"""
        <div style="padding: 10px; background: rgba(5,150,105,0.1); border:1px solid rgba(5,150,105,0.2); border-radius:10px; margin-bottom:12px;">
            <div style="font-size:12px; color:#6ee7b7; font-weight:700;">✅ Phiên hiện tại</div>
            <div style="font-size:22px; font-weight:900; color:#34d399;">{st.session_state.success_count}</div>
            <div style="font-size:11px; color:#475569;">ảnh đã xử lý thành công</div>
        </div>
        """, unsafe_allow_html=True)

    if st.button("🚪  Đăng xuất", use_container_width=True):
        for k in list(defaults.keys()):
            st.session_state[k] = defaults[k]
        st.rerun()

# Clear results on menu change
if st.session_state.current_menu != menu:
    st.session_state.thumb_results = []
    st.session_state.thumb_zip = None
    st.session_state.success_count = 0
    st.session_state.preview_images = []
    st.session_state.current_menu = menu

# ==========================================
# PAGE: TRANG CHỦ
# ==========================================
if "Trang Chủ" in menu:
    st.markdown("""
    <div class="page-title">🌟 Tổng Quan Hệ Thống</div>
    <div class="page-subtitle">Chào mừng đến với Đức Content Pro — nền tảng thu thập & xử lý ảnh sản phẩm</div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("🏪 Nguồn hỗ trợ", "3", "DMX · TGDD · Link")
    with c2:
        st.metric("🖼️ Xử lý logo", "✅ Có", "PNG nền trong suốt")
    with c3:
        st.metric("💾 Xuất file", "ZIP", "JPEG quality 92")
    with c4:
        st.metric("👥 Tài khoản", str(len(USERS)), "Người dùng đã đăng ký")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="pro-card">
            <div style="font-size:16px; font-weight:800; color:#e2e8f0; margin-bottom:12px;">📌 Hướng dẫn sử dụng</div>
            <div style="font-size:13px; line-height:2; color:#64748b;">
                <b style="color:#93c5fd;">Bước 1:</b> Chọn nguồn thu ảnh từ menu bên trái<br>
                <b style="color:#93c5fd;">Bước 2:</b> Upload logo/khung PNG (nền trong suốt)<br>
                <b style="color:#93c5fd;">Bước 3:</b> Dán danh sách ID hoặc link ảnh<br>
                <b style="color:#93c5fd;">Bước 4:</b> Cấu hình tùy chọn xử lý ảnh<br>
                <b style="color:#93c5fd;">Bước 5:</b> Nhấn LUYỆN CÔNG & tải về file ZIP
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="pro-card">
            <div style="font-size:16px; font-weight:800; color:#e2e8f0; margin-bottom:12px;">⚡ Tính năng nổi bật</div>
            <div style="font-size:13px; line-height:2; color:#64748b;">
                ✅ Thu ảnh thumbnail chất lượng cao<br>
                ✅ Ghép logo/khung lên ảnh tự động<br>
                ✅ Watermark text tùy chỉnh<br>
                ✅ Điều chỉnh độ sáng & sharpen<br>
                ✅ Preview ảnh trực tiếp trên web<br>
                ✅ Xuất ZIP một lần tải về
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.info("💡 **Mẹo**: Để thu ảnh nhanh hơn, hãy chuẩn bị sẵn file cookies JSON và đặt vào thư mục gốc của app.")

# ==========================================
# PAGE: THU ẢNH DMX / TGDD
# ==========================================
elif "Thu Ảnh —" in menu and "Link" not in menu:
    domain = "dienmayxanh.com" if "DienmayXanh" in menu else "thegioididong.com"
    brand = "DMX" if "DienmayXanh" in menu else "TGDD"
    accent = "#0088FF" if brand == "DMX" else "#FFCA28"
    label = "Điện Máy Xanh" if brand == "DMX" else "Thế Giới Di Động"

    st.markdown(f"""
    <div class="page-title" style="color:{accent};">📸 Thu Ảnh — {label}</div>
    <div class="page-subtitle">Tự động lấy thumbnail sản phẩm từ {domain}</div>
    """, unsafe_allow_html=True)

    # ---- BƯỚC 1: Upload Logo ----
    st.markdown('<div class="step-label">Bước 1 — Logo / Khung</div>', unsafe_allow_html=True)
    uploaded_logo = st.file_uploader(
        "Upload logo hoặc khung PNG (nền trong suốt, tỷ lệ 1:1 khuyến nghị)",
        type=["png"], key=f"logo_{brand}"
    )
    logo_img = None
    if uploaded_logo:
        logo_img = Image.open(uploaded_logo).convert("RGBA")
        st.success(f"✅ Đã tải logo: **{uploaded_logo.name}** ({logo_img.size[0]}×{logo_img.size[1]}px)")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ---- BƯỚC 2: Tùy chọn xử lý ----
    st.markdown('<div class="step-label">Bước 2 — Tùy Chọn Xử Lý Ảnh</div>', unsafe_allow_html=True)
    opt1, opt2, opt3 = st.columns(3)
    with opt1:
        watermark_text = st.text_input("💬 Watermark text (để trống nếu không cần)", placeholder="VD: @ducontent")
    with opt2:
        brightness = st.slider("☀️ Độ sáng ảnh", 0.5, 2.0, 1.0, 0.05)
    with opt3:
        sharpen = st.checkbox("🔍 Làm nét ảnh (Sharpen)", value=False)
        img_quality = st.slider("🎨 Chất lượng JPEG", 70, 100, 92, 1)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ---- BƯỚC 3: Nhập ID ----
    st.markdown('<div class="step-label">Bước 3 — Danh Sách ID Sản Phẩm</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 2.5])

    with col1:
        raw_input = st.text_area(
            "Dán danh sách ID (mỗi ID một dòng):",
            height=280,
            placeholder="Ví dụ:\n234766\n174900\n..."
        )
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            btn_run = st.button("🚀 LUYỆN CÔNG", type="primary", use_container_width=True)
        with col_b2:
            btn_clear = st.button("🗑️ Xóa kết quả", use_container_width=True)

        if btn_clear:
            st.session_state.thumb_results = []
            st.session_state.thumb_zip = None
            st.session_state.success_count = 0
            st.session_state.preview_images = []
            st.rerun()

        if raw_input.strip():
            ids = [l.strip() for l in raw_input.splitlines() if l.strip()]
            st.markdown(f'<span class="stat-badge badge-info">📋 {len(ids)} ID</span>', unsafe_allow_html=True)

    with col2:
        if btn_run:
            if not raw_input.strip():
                st.warning("⚠️ Vui lòng nhập ít nhất 1 ID!")
            else:
                ids = [l.strip() for l in raw_input.splitlines() if l.strip()]
                temp_results = []
                preview_images = []
                zip_buffer = io.BytesIO()
                success_count = 0
                fail_count = 0

                progress_text = st.empty()
                progress_bar = st.progress(0)
                status_cols = st.columns(3)
                metric_ok = status_cols[0].empty()
                metric_fail = status_cols[1].empty()
                metric_pct = status_cols[2].empty()
                
                session = get_session()

                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for i, pid in enumerate(ids):
                        m = re.search(r'(\d+)(?!.*\d)', pid)
                        pid_num = m.group(1) if m else pid

                        progress_text.markdown(f"⏳ Đang xử lý: **{pid_num}** &nbsp;({i+1}/{len(ids)})")

                        final_url, thumb, _ = fetch_by_page(session, pid_num, domain)
                        if not (thumb and _.startswith("OK(Page-og")):
                            a_url, a_img, _ = fetch_by_api(session, pid_num, domain)
                            final_url = final_url or a_url or f"https://www.{domain}/sp-{pid_num}"
                            thumb = a_img or thumb

                        thumb_clean = clean_image_url(thumb, domain) if thumb else ""
                        dl_status = "Không có ảnh"

                        if thumb_clean:
                            try:
                                img_resp = session.get(thumb_clean, timeout=15)
                                if img_resp.status_code == 200:
                                    base_img = Image.open(io.BytesIO(img_resp.content))
                                    processed = process_image(base_img, logo_img, watermark_text, brightness, sharpen)
                                    img_bytes = img_to_bytes(processed, img_quality)
                                    zf.writestr(f"{pid_num}.jpg", img_bytes)
                                    success_count += 1
                                    dl_status = "✅ Thành công"

                                    # Lưu preview (tối đa 12 ảnh)
                                    if len(preview_images) < 12:
                                        b64 = base64.b64encode(img_bytes).decode()
                                        preview_images.append((pid_num, b64))
                                else:
                                    fail_count += 1
                                    dl_status = f"❌ HTTP {img_resp.status_code}"
                            except Exception as ex:
                                fail_count += 1
                                dl_status = f"❌ Lỗi: {str(ex)[:40]}"
                        else:
                            fail_count += 1

                        temp_results.append({
                            "ID": pid_num,
                            "Link SP": final_url or f"https://www.{domain}/sp-{pid_num}",
                            "Link Ảnh": thumb_clean,
                            "Trạng Thái": dl_status,
                        })

                        pct = (i + 1) / len(ids)
                        progress_bar.progress(pct)
                        metric_ok.metric("✅ Thành công", success_count)
                        metric_fail.metric("❌ Thất bại", fail_count)
                        metric_pct.metric("📊 Tiến độ", f"{pct*100:.0f}%")
                        time.sleep(0.1)

                progress_text.success(f"🎉 Hoàn thành! {success_count}/{len(ids)} ảnh xử lý thành công.")
                st.session_state.thumb_results = temp_results
                st.session_state.thumb_zip = zip_buffer.getvalue()
                st.session_state.success_count = success_count
                st.session_state.preview_images = preview_images

        # HIỂN THỊ KẾT QUẢ
        if st.session_state.thumb_results:
            if st.session_state.success_count > 0:
                st.download_button(
                    label=f"📦 Tải xuống {st.session_state.success_count} ảnh (ZIP)",
                    data=st.session_state.thumb_zip,
                    file_name=f"Anh_{brand}_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                    mime="application/zip",
                    type="primary",
                    use_container_width=True
                )
            else:
                st.error("❌ Không có ảnh nào tải thành công. Kiểm tra lại ID hoặc Cookie!")

            # Preview grid
            if st.session_state.preview_images:
                st.markdown("**🖼️ Preview ảnh đã xử lý:**")
                cols = st.columns(4)
                for idx, (pid, b64) in enumerate(st.session_state.preview_images):
                    with cols[idx % 4]:
                        st.image(f"data:image/jpeg;base64,{b64}", caption=pid, use_container_width=True)

            # Table
            tab_table, tab_copy = st.tabs(["📋 Bảng kết quả", "📝 Copy dữ liệu"])
            with tab_table:
                df = pd.DataFrame(st.session_state.thumb_results)
                st.dataframe(df, use_container_width=True, height=350)
            with tab_copy:
                lines = ["ID\tLink SP\tLink Ảnh\tTrạng Thái"]
                for r in st.session_state.thumb_results:
                    lines.append(f"{r['ID']}\t{r['Link SP']}\t{r['Link Ảnh']}\t{r['Trạng Thái']}")
                st.code("\n".join(lines), language="text")

# ==========================================
# PAGE: THU ẢNH LINK TRỰC TIẾP
# ==========================================
elif "Link Trực Tiếp" in menu:
    st.markdown("""
    <div class="page-title" style="color:#10b981;">🔗 Thu Ảnh — Link Trực Tiếp</div>
    <div class="page-subtitle">Tải và xử lý ảnh từ URL trực tiếp (hỗ trợ dán dính liền)</div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="step-label">Bước 1 — Logo / Khung</div>', unsafe_allow_html=True)
    uploaded_logo = st.file_uploader("Upload logo hoặc khung PNG", type=["png"], key="logo_direct")
    logo_img = None
    if uploaded_logo:
        logo_img = Image.open(uploaded_logo).convert("RGBA")
        st.success(f"✅ Đã tải: **{uploaded_logo.name}**")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="step-label">Bước 2 — Tùy Chọn</div>', unsafe_allow_html=True)

    opt1, opt2, opt3 = st.columns(3)
    with opt1:
        watermark_text = st.text_input("💬 Watermark text", placeholder="VD: @ducontent", key="wm_direct")
    with opt2:
        brightness = st.slider("☀️ Độ sáng", 0.5, 2.0, 1.0, 0.05, key="br_direct")
    with opt3:
        sharpen = st.checkbox("🔍 Sharpen", key="sh_direct")
        img_quality = st.slider("🎨 JPEG Quality", 70, 100, 92, 1, key="q_direct")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="step-label">Bước 3 — Link Ảnh</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2.5])
    with col1:
        raw_input = st.text_area(
            "Dán link ảnh vào đây (có thể dán dính liền nhau):",
            height=280,
            placeholder="https://cdn.example.com/img1.jpg\nhttps://cdn.example.com/img2.jpg\n..."
        )
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            btn_run = st.button("🚀 LUYỆN CÔNG", type="primary", use_container_width=True, key="btn_direct")
        with col_b2:
            if st.button("🗑️ Xóa", use_container_width=True, key="clear_direct"):
                st.session_state.thumb_results = []
                st.session_state.thumb_zip = None
                st.session_state.success_count = 0
                st.session_state.preview_images = []
                st.rerun()

    with col2:
        if btn_run:
            if not raw_input.strip():
                st.warning("⚠️ Vui lòng nhập ít nhất 1 link ảnh!")
            else:
                links = re.findall(r'https?://(?:(?!https?://).)*?\.(?:jpg|jpeg|png|webp)', raw_input, re.IGNORECASE)
                if not links:
                    links = [l.strip() for l in raw_input.splitlines() if l.strip().startswith("http")]
                if not links:
                    st.warning("⚠️ Không tìm thấy link ảnh hợp lệ!")
                else:
                    temp_results = []
                    preview_images = []
                    zip_buffer = io.BytesIO()
                    success_count = 0
                    fail_count = 0

                    progress_text = st.empty()
                    progress_bar = st.progress(0)
                    mc = st.columns(3)
                    m_ok = mc[0].empty()
                    m_fail = mc[1].empty()
                    m_pct = mc[2].empty()

                    session = get_session()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                        for i, url in enumerate(links):
                            fm = re.search(r'/([^/]+\.(?:jpg|jpeg|png|webp))', url, re.IGNORECASE)
                            file_name = fm.group(1) if fm else f"image_{i+1}.jpg"
                            pid = file_name.split(".")[0][:20]

                            progress_text.markdown(f"⏳ Đang tải: **{file_name}** ({i+1}/{len(links)})")

                            dl_status = "Không có ảnh"
                            try:
                                resp = session.get(url, timeout=15)
                                if resp.status_code == 200:
                                    base_img = Image.open(io.BytesIO(resp.content))
                                    processed = process_image(base_img, logo_img, watermark_text, brightness, sharpen)
                                    img_bytes = img_to_bytes(processed, img_quality)
                                    out_name = f"{i+1:04d}_{file_name.rsplit('.', 1)[0]}.jpg"
                                    zf.writestr(out_name, img_bytes)
                                    success_count += 1
                                    dl_status = "✅ Thành công"
                                    if len(preview_images) < 12:
                                        b64 = base64.b64encode(img_bytes).decode()
                                        preview_images.append((pid, b64))
                                else:
                                    fail_count += 1
                                    dl_status = f"❌ HTTP {resp.status_code}"
                            except Exception as ex:
                                fail_count += 1
                                dl_status = f"❌ Lỗi: {str(ex)[:40]}"

                            temp_results.append({
                                "ID": pid, "Link SP": "—", "Link Ảnh": url, "Trạng Thái": dl_status
                            })

                            pct = (i + 1) / len(links)
                            progress_bar.progress(pct)
                            m_ok.metric("✅ OK", success_count)
                            m_fail.metric("❌ Lỗi", fail_count)
                            m_pct.metric("📊 Tiến độ", f"{pct*100:.0f}%")
                            time.sleep(0.08)

                    progress_text.success(f"🎉 Xong! {success_count}/{len(links)} ảnh thành công.")
                    st.session_state.thumb_results = temp_results
                    st.session_state.thumb_zip = zip_buffer.getvalue()
                    st.session_state.success_count = success_count
                    st.session_state.preview_images = preview_images

        if st.session_state.thumb_results:
            if st.session_state.success_count > 0:
                st.download_button(
                    label=f"📦 Tải {st.session_state.success_count} ảnh (ZIP)",
                    data=st.session_state.thumb_zip,
                    file_name=f"Anh_Links_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                    mime="application/zip",
                    type="primary",
                    use_container_width=True
                )
            else:
                st.error("❌ Không tải được ảnh nào. Kiểm tra lại link!")

            if st.session_state.preview_images:
                st.markdown("**🖼️ Preview:**")
                cols = st.columns(4)
                for idx, (pid, b64) in enumerate(st.session_state.preview_images):
                    with cols[idx % 4]:
                        st.image(f"data:image/jpeg;base64,{b64}", caption=pid, use_container_width=True)

            tab1, tab2 = st.tabs(["📋 Bảng kết quả", "📝 Copy"])
            with tab1:
                st.dataframe(pd.DataFrame(st.session_state.thumb_results), use_container_width=True, height=350)
            with tab2:
                lines = ["ID\tLink Ảnh\tTrạng Thái"]
                for r in st.session_state.thumb_results:
                    lines.append(f"{r['ID']}\t{r['Link Ảnh']}\t{r['Trạng Thái']}")
                st.code("\n".join(lines), language="text")

# ==========================================
# PAGE: GOOGLE SHEET (ADMIN)
# ==========================================
elif "Google Sheet" in menu and is_admin:
    st.markdown("""
    <div class="page-title">📊 Quản Lý Google Sheet</div>
    <div class="page-subtitle">Kết nối trực tiếp và lọc dữ liệu từ Google Sheet hệ thống</div>
    """, unsafe_allow_html=True)

    SHEET_ID = "1wtIhG3O1_oDrJcUvgwxcjxeRnrWpqbWIN15c4a37kl0"
    CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=0"

    c1, c2 = st.columns([2, 1])
    with c1:
        custom_url = st.text_input("🔗 URL Google Sheet CSV (để trống = dùng Sheet mặc định):", placeholder=CSV_URL)
    with c2:
        btn_load = st.button("🔄 Tải dữ liệu", type="primary", use_container_width=True)
        st.markdown("")

    fetch_url = custom_url.strip() if custom_url.strip() else CSV_URL

    with st.spinner("⏳ Đang tải dữ liệu..."):
        try:
            df_raw = pd.read_csv(fetch_url)
            if df_raw.iloc[:, 0].dtype == object:
                df_raw.iloc[:, 0] = pd.to_datetime(df_raw.iloc[:, 0], errors="coerce")

            creator_col = df_raw.columns[28] if len(df_raw.columns) > 28 else df_raw.columns[-1]

            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            st.markdown("### 🔍 Bộ lọc")
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                creators = ["Tất cả"] + sorted(df_raw[creator_col].dropna().astype(str).unique().tolist())
                creator_filter = st.selectbox("👨‍💻 Người làm:", creators)
            with fc2:
                kw = st.text_input("🔎 Tìm theo tên sản phẩm:")
            with fc3:
                sort_col = st.selectbox("⬇️ Sắp xếp theo:", ["—"] + list(df_raw.columns))

            df_filtered = df_raw.copy()
            if creator_filter != "Tất cả":
                df_filtered = df_filtered[df_filtered[creator_col].astype(str) == creator_filter]
            if kw:
                df_filtered = df_filtered[df_filtered.iloc[:, 3].astype(str).str.lower().str.contains(kw.lower(), na=False)]
            if sort_col != "—":
                df_filtered = df_filtered.sort_values(by=sort_col, ascending=False)

            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            m1, m2, m3 = st.columns(3)
            m1.metric("📋 Tổng dòng", len(df_filtered))
            m2.metric("📁 Tổng cột", len(df_filtered.columns))
            m3.metric("👥 Người làm", df_raw[creator_col].nunique())

            st.dataframe(df_filtered, use_container_width=True, height=500)

            # Export CSV
            csv_bytes = df_filtered.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📥 Xuất CSV đã lọc", csv_bytes, f"sheet_export_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

        except Exception as e:
            st.error(f"❌ Lỗi tải Google Sheet: {e}")
            st.info("💡 Hãy đảm bảo Sheet đã được chia sẻ công khai (Anyone with the link can view).")

# ==========================================
# PAGE: QUẢN LÝ TÀI KHOẢN (ADMIN)
# ==========================================
elif "Tài Khoản" in menu and is_admin:
    st.markdown("""
    <div class="page-title">👥 Quản Lý Tài Khoản</div>
    <div class="page-subtitle">Xem, thêm và xóa tài khoản trong hệ thống</div>
    """, unsafe_allow_html=True)

    st.markdown(f'<span class="stat-badge badge-info">👥 {len(USERS)} tài khoản</span>', unsafe_allow_html=True)
    st.markdown("")

    # Hiển thị danh sách
    user_list = [{"Tên đăng nhập": u, "Loại": "Admin" if u == "ducpro" else "User"} for u in USERS]
    st.dataframe(pd.DataFrame(user_list), use_container_width=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### ➕ Thêm tài khoản mới")
        with st.form("admin_add_user"):
            nu = st.text_input("Tên đăng nhập")
            np = st.text_input("Mật khẩu", type="password")
            if st.form_submit_button("✅ Thêm", use_container_width=True):
                u = nu.strip()
                p = np.strip()
                if len(u) < 3 or len(p) < 6:
                    st.warning("Tên ≥ 3 ký tự, mật khẩu ≥ 6 ký tự!")
                elif u in USERS:
                    st.error("Tên đã tồn tại!")
                else:
                    USERS[u] = hash_password(p)
                    save_users(USERS)
                    st.success(f"✅ Đã thêm: **{u}**")
                    st.rerun()

    with c2:
        st.markdown("#### 🗑️ Xóa tài khoản")
        protected = {"ducpro", "tuanpro"}
        deletable = [u for u in USERS if u not in protected]
        if deletable:
            del_user = st.selectbox("Chọn tài khoản:", deletable)
            if st.button("🗑️ Xóa tài khoản này", type="primary"):
                del USERS[del_user]
                save_users(USERS)
                st.success(f"✅ Đã xóa: **{del_user}**")
                st.rerun()
        else:
            st.info("Không có tài khoản nào có thể xóa.")
