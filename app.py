import streamlit as st
import json
import os
import calendar
from openai import OpenAI
from datetime import datetime, date
import database.db_manager as db
from streamlit_mic_recorder import mic_recorder
from faster_whisper import WhisperModel
import components.sticker_canvas as canvas_comp

# 1. SAYFA YAPILANDIRMASI
ICON_PATH = os.path.join(os.path.dirname(__file__), "assets", "bujo_icon.png")
st.set_page_config(
    page_title="Bujo",
    page_icon=ICON_PATH if os.path.exists(ICON_PATH) else "✍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. CSS STİL DOSYASINI YÜKLE
CSS_FILE = os.path.join(os.path.dirname(__file__), "assets", "bujo_style.css")
if os.path.exists(CSS_FILE):
    with open(CSS_FILE, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Mikrofon ve Özel Komut Paneli Stilleri
st.markdown("""
<style>
    div[element-id*="recorder_minimal"] button {
        font-family: 'Patrick Hand', cursive !important;
        font-size: 22px !important;
        padding: 12px 28px !important;
        border-radius: 14px !important;
        background-color: #E53935 !important;
        color: white !important;
        border: 2px solid #B71C1C !important;
        box-shadow: 4px 4px 0px #795548 !important;
        width: 100% !important;
    }
    
    .ai-command-card {
        background: #FFFDE7 !important;
        border: 3px solid #8D6E63 !important;
        border-radius: 18px !important;
        padding: 20px !important;
        box-shadow: 6px 6px 16px rgba(74, 62, 61, 0.12) !important;
        margin-top: 15px !important;
        position: relative !important;
    }

    .mini-moon-widget {
        background: #FFF9C4 !important;
        border: 2px dashed #8D6E63 !important;
        border-radius: 12px !important;
        padding: 10px !important;
        text-align: center !important;
        margin-bottom: 15px !important;
    }
</style>
""", unsafe_allow_html=True)

INFO_FILE = "foundry_service_info.json"

@st.cache_resource
def init_foundry_local():
    try:
        with open(INFO_FILE, "r") as f:
            info = json.load(f)
    except FileNotFoundError:
        st.error("⚠️ Foundry Local servisi çalışmıyor gibi görünüyor. Önce start_service.py'yi başlatın.")
        st.stop()

    client = OpenAI(base_url=info["base_url"], api_key="none")
    try:
        client.models.list()
    except Exception:
        st.error("⚠️ Servise bağlanılamadı. start_service.py'nin hâlâ çalıştığından emin olun.")
        st.stop()

    return client, info["model_id"]

client, FOUNDRY_MODEL_ID = init_foundry_local()

db.init_db()

@st.cache_resource
def load_whisper():
    return WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")

whisper_model = load_whisper()

user_profile = db.get_profile_db()

HOBBY_OPTIONS = [
    "🏋️‍♂️ Spor & Fitness", "💻 Yazılım & Kodlama", "📚 Kitap Okuma", 
    "🎬 Sinema & Dizi", "🎮 Dijital Oyunlar", "✈️ Seyahat & Gezi", 
    "🎵 Müzik & Enstrüman", "🎨 Resim & Tasarım", "🍳 Yemek Pişirme", "🧘 Meditasyon & Yoga"
]

ASSISTANT_STYLES = [
    "🔥 Sert & Disiplinli Koç (Seni zorlar ve hedeflerine odaklandırır)",
    "☕ Empatik & Dostça (Sıcak, dinleyici ve destekleyici)",
    "🧠 Socrates Tarzı Sorgulayıcı (Sorular sorarak düşünmeni sağlar)",
    "⚡ Kısa & Sonuç Odaklı Profesyonel (Lafı uzatmaz, doğrudan cevaba odaklanır)"
]

RESPONSE_LENGTHS = [
    "Kısa & Öz (1-2 Cümle)",
    "Dengeli (Standard)",
    "Detaylı & Açıklayıcı (Uzun Yanıtlar)"
]

STICKER_CATEGORIES = {
    "😊 Duygular (Mood)": [
        ("happy", "😄 Mutlu", "mood"),
        ("sad", "😢 Üzgün", "mood"),
        ("excited", "🤩 Heyecanlı", "mood"),
        ("tired", "😴 Yorgun", "mood"),
        ("calm", "🧘 Sakin", "mood"),
        ("star", "⭐ Yıldız", "mood"),
        ("heart", "❤️ Kalp", "mood")
    ],
    "☀️ Hava Durumu": [
        ("sunny", "☀️ Güneşli", "weather"),
        ("rainy", "🌧️ Yağmurlu", "weather"),
        ("cloudy", "☁️ Bulutlu", "weather"),
        ("snowy", "❄️ Karlı", "weather")
    ],
    "☕ Kahve & Yiyecek": [
        ("coffee", "☕ Kahve", "food"),
        ("tea", "🍵 Çay", "food"),
        ("croissant", "🥐 Kruvasan", "food"),
        ("pizza", "🍕 Pizza", "food"),
        ("cake", "🍰 Pasta", "food")
    ],
    "🎀 Bantlar & Ataçlar": [
        ("washi_pink", "🎀 Pembe Bant", "tapes"),
        ("washi_yellow", "🟡 Sarı Bant", "tapes"),
        ("paperclip", "📎 Ataç", "tapes"),
        ("pushpin", "📍 İğne", "tapes")
    ],
    "🐱 Sevimli İkonlar": [
        ("cat", "🐱 Kedi", "cute"),
        ("flower", "🌸 Çiçek", "cute"),
        ("camera", "📷 Kamera", "cute"),
        ("book", "📖 Kitap", "cute"),
        ("cinema", "🎟️ Bilet", "cute")
    ]
}

STICKER_MAPPING = {
    "kahve": ("coffee", "food"),
    "coffee": ("coffee", "food"),
    "çay": ("tea", "food"),
    "kruvasan": ("croissant", "food"),
    "pizza": ("pizza", "food"),
    "pasta": ("cake", "food"),
    "tatlı": ("cake", "food"),
    "sinema": ("cinema", "cute"),
    "film": ("cinema", "cute"),
    "bilet": ("cinema", "cute"),
    "kitap": ("book", "cute"),
    "kedi": ("cat", "cute"),
    "fotoğraf": ("camera", "cute"),
    "çiçek": ("flower", "cute"),
    "mutlu": ("happy", "mood"),
    "harika": ("happy", "mood"),
    "üzgün": ("sad", "mood"),
    "heyecanlı": ("excited", "mood"),
    "yorgun": ("tired", "mood"),
    "sakin": ("calm", "mood"),
    "güneş": ("sunny", "weather"),
    "yağmur": ("rainy", "weather"),
    "bulut": ("cloudy", "weather"),
    "kar": ("snowy", "weather")
}

def get_moon_phase(dt=None):
    if dt is None:
        dt = date.today()
    diff = (dt - date(2001, 1, 1)).days
    moon_age = (diff + 4.8) % 29.53058867
    if moon_age < 1.84566: return "🌑 Yeni Ay"
    elif moon_age < 5.53699: return "🌒 Hilal"
    elif moon_age < 9.22831: return "🌓 İlk Dördün"
    elif moon_age < 12.91963: return "🌔 Büyüyen Ay"
    elif moon_age < 16.61096: return "🌕 Dolunay"
    elif moon_age < 20.30228: return "🌖 Küçülen Ay"
    elif moon_age < 23.99361: return "🌗 Son Dördün"
    else: return "🌘 Son Hilal"

# --- EĞİTİM EKRANI ---
if not user_profile:
    st.title("📖 Dijital Bullet Journal'ına Hoş Geldin!")
    st.markdown("Defter kapağını ve kişisel indeksini oluşturarak başlayalım:")

    with st.form("onboarding_form"):
        name = st.text_input("Adın nedir?", placeholder="Örn: Ahmet")
        gender = st.selectbox("Cinsiyetiniz:", ["Erkek", "Kadın", "Belirtmek İstemiyorum"])
        birth_date = st.date_input("Doğum Tarihin", min_value=date(1950, 1, 1), max_value=date.today())
        height = st.number_input("Boyun (cm)", min_value=100, max_value=230, value=175)
        weight = st.number_input("Kilon (kg)", min_value=30.0, max_value=200.0, value=70.0)
        occupation = st.text_input("Mesleğin / Okulun?", placeholder="Örn: Yazılım Mühendisi")
        selected_hobbies = st.multiselect("Hobilerin nelerdir?", options=HOBBY_OPTIONS)
        about_me = st.text_area("Hakkında bilmem gerekenler", placeholder="Serbest metin...")
        assistant_style = st.selectbox("Asistan üslubu nasıl olsun?", options=ASSISTANT_STYLES)
        response_length = st.selectbox("Cevap Uzunluğu Tercihi:", options=RESPONSE_LENGTHS)
        ai_rules = st.text_area("Yapay Zekaya Özel Kurallar:", placeholder="Özel kurallarınız...")

        submitted = st.form_submit_button("Defteri Aç ve Başla ✍️")
        if submitted and name:
            profile_data = {
                "name": name,
                "gender": gender,
                "birth_date": str(birth_date),
                "height": height,
                "weight": weight,
                "occupation": occupation,
                "hobbies": selected_hobbies,
                "about_me": about_me,
                "assistant_style": assistant_style,
                "response_length": response_length,
                "ai_rules": ai_rules
            }
            db.save_profile_db(profile_data)
            st.rerun()

# --- ANA UYGULAMA ---
else:
    modules_status = db.get_active_modules()
    custom_trackers = db.get_all_custom_trackers()

    today_str = str(date.today())
    if "diary_chat_date" not in st.session_state:
        st.session_state["diary_chat_date"] = today_str

    if st.session_state["diary_chat_date"] != today_str:
        st.session_state["diary_chat_date"] = today_str
        st.session_state.diary_messages = [
            {"role": "assistant", "content": f"Günaydın {user_profile['name']}! ☕ Günün Bullet Journal sayfana bugünü not etmeye hazır mısın?"}
        ]

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"""
        <div class="user-profile-card">
            <h3>📖 {user_profile['name']}</h3>
            <p>💼 {user_profile['occupation']}</p>
            <p>🤖 {user_profile['assistant_style'].split('(')[0]}</p>
        </div>
        """, unsafe_allow_html=True)

        page = st.radio(
            "📌 Gezinme İndeksi",
            options=[
                "🎙️ Günün Defter Yaprağı", 
                "💬 Çalışmalarım", 
                "📅 Ajanda", 
                "📚 Okuma & İzleme Rafı", 
                "⚙️ Defter Ayarları & İndeks"
            ]
        )

        st.divider()

        # SIDEBAR'DA STICKER VE SÜSLEME ARAÇLARI
        if page == "🎙️ Günün Defter Yaprağı":
            # MİNİK AY TAKVİMİ & FAZI WIDGET
            moon = get_moon_phase()
            today_d = date.today()
            st.markdown(f"""
            <div class="mini-moon-widget">
                <div style="font-size: 22px; font-weight: bold; color: #5D4037;">{moon}</div>
                <div style="font-size: 15px; color: #8D6E63;">🗓️ {today_d.strftime('%d %B %Y')}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("### 🎨 Sticker'lar")

            selected_st_cat = st.selectbox("Kategori:", list(STICKER_CATEGORIES.keys()))
            cat_stickers = STICKER_CATEGORIES[selected_st_cat]

            st_cols = st.columns(2)
            for idx, (st_key, st_name, st_cat) in enumerate(cat_stickers):
                c_idx = idx % 2
                if st_cols[c_idx].button(st_name, key=f"sb_st_btn_{st_key}", use_container_width=True):
                    current_stickers = db.get_stickers_for_date(today_str)
                    pos_x = 40 + (len(current_stickers) * 45) % 360
                    pos_y = 60 + (len(current_stickers) // 8) * 60
                    db.add_sticker_entry(today_str, st_key, st_cat, pos_x=pos_x, pos_y=pos_y)
                    st.rerun()

            st.divider()

            with st.expander("✍️ Not Ekle"):
                with st.form("custom_text_sticker_form", clear_on_submit=True):
                    txt_sticker = st.text_input("Metin / Not:", placeholder="")
                    col_clr, col_fnt = st.columns(2)
                    with col_clr:
                        txt_color = st.selectbox("Renk", ["Sarı 🟡", "Pembe 🌸", "Yeşil 🌿", "Mavi 💧", "Mor 🍇"], key="st_clr_sel")
                    with col_fnt:
                        txt_font = st.selectbox("Font", ["Caveat", "Patrick Hand", "Kalam", "Outfit"], key="st_fnt_sel")
                    if st.form_submit_button("Sayfaya Yapıştır 📌", use_container_width=True) and txt_sticker.strip():
                        color_code = "yellow"
                        if "Pembe" in txt_color: color_code = "pink"
                        elif "Yeşil" in txt_color: color_code = "green"
                        elif "Mavi" in txt_color: color_code = "blue"
                        elif "Mor" in txt_color: color_code = "purple"

                        current_stickers = db.get_stickers_for_date(today_str)
                        pos_x = 50 + (len(current_stickers) * 45) % 360
                        pos_y = 70 + (len(current_stickers) // 8) * 60
                        db.add_sticker_entry(today_str, f"text:{color_code}:{txt_font}:{txt_sticker.strip()}", "text", pos_x=pos_x, pos_y=pos_y)
                        st.rerun()

            st.divider()
            
            placed_stickers = db.get_stickers_for_date(today_str)
            if placed_stickers:
                if st.button("🧹 Tüm Sticker'ları Temizle", use_container_width=True):
                    db.clear_stickers_for_date(today_str)
                    st.rerun()

        elif page == "💬 Çalışmalarım":
            st.subheader("🗂️ Sohbet Odaları")
            if st.button("➕ Yeni Not Odası", use_container_width=True):
                chat_sessions = db.get_all_chat_sessions()
                new_id = db.create_chat_session(f"Sohbet #{len(chat_sessions) + 1}")
                st.session_state["active_chat_id"] = new_id
                st.rerun()

            st.divider()
            chat_sessions = db.get_all_chat_sessions()
            if chat_sessions:
                for sess in chat_sessions:
                    is_active = st.session_state.get("active_chat_id") == sess["id"]
                    btn_label = f"📌 {sess['title']}" if is_active else f"💬 {sess['title']}"
                    
                    c1, c2, c3 = st.columns([3, 1, 1])
                    if c1.button(btn_label, key=f"sess_btn_{sess['id']}", use_container_width=True):
                        st.session_state["active_chat_id"] = sess["id"]
                        st.rerun()
                    
                    with c2:
                        with st.popover("✏️"):
                            st.caption("Oda İsmini Değiştir")
                            new_sb_title = st.text_input("Yeni isim:", value=sess['title'], key=f"sb_ren_{sess['id']}")
                            if st.button("Kaydet", key=f"sb_sav_{sess['id']}"):
                                if new_sb_title.strip():
                                    db.update_chat_session_title(sess['id'], new_sb_title)
                                    st.rerun()

                    with c3:
                        if st.button("🗑️", key=f"del_sess_{sess['id']}"):
                            db.delete_chat_session(sess["id"])
                            if st.session_state.get("active_chat_id") == sess["id"]:
                                st.session_state["active_chat_id"] = None
                            st.rerun()

        elif page == "📚 Okuma & İzleme Rafı":
            st.subheader("🎯 Medya Filtreleri")
            media_type_filter = st.selectbox("Tür:", ["Tümü", "🎬 Film", "📺 Dizi", "📖 Kitap"])
            media_status_filter = st.radio("Durum:", ["Hepsi", "✅ Tamamlananlar", "📌 İstek Listesi"])
            st.session_state["media_type_filter"] = media_type_filter
            st.session_state["media_status_filter"] = media_status_filter

    # =========================================================================
    # SAYFA 1: 🎙️ GÜNÜN DEFTER YAPRAĞI (VOICE DIARY & BULLET JOURNAL SPREAD)
    # =========================================================================
    if page == "🎙️ Günün Defter Yaprağı":
        st.markdown("<div class='spiral-ring-bar'></div>", unsafe_allow_html=True)
        st.title("📖 Günün Bullet Journal Defter Yaprağı")
        st.caption(f"🗓️ Bugünün Tarihi: **{date.today().strftime('%d %B %Y')}**")

        # SOL VE SAĞ DEFTER SAYFASI YAPISI
        left_col, right_col = st.columns([1.6, 1])

        # SOL SAYFA: STICKER CANVAS & DIARY LOGS
        with left_col:
            st.markdown("""
            <div class="bujo-paper-card">
                <div class="washi-tape-pink"></div>
                <div class="washi-tape-yellow"></div>
                <h3 style="margin-top: 5px;">✍️ Günün Defter Sayfası</h3>
            </div>
            """, unsafe_allow_html=True)

            # STICKER CANVAS İNTERAKTİF BİLEŞENİ
            canvas_action = canvas_comp.render_sticker_canvas(today_str)
            if canvas_action and isinstance(canvas_action, dict):
                action_sig = json.dumps(canvas_action, sort_keys=True)
                if st.session_state.get("last_canvas_action_sig") != action_sig:
                    st.session_state["last_canvas_action_sig"] = action_sig
                    act = canvas_action.get("action")
                    if act == "move":
                        db.update_sticker_position(canvas_action["id"], canvas_action["pos_x"], canvas_action["pos_y"])
                        st.rerun()
                    elif act == "delete":
                        db.delete_sticker_entry(canvas_action["id"])
                        st.rerun()
                    elif act == "scale":
                        db.update_sticker_scale(canvas_action["id"], canvas_action["scale"])
                        st.rerun()

            st.divider()

            today_diaries = db.get_today_diary_entries()
            if today_diaries:
                st.markdown("### 📝 Bugün Deftere Yazılanlar")
                for td in today_diaries:
                    st.markdown(f"""
                    <div class="postit-yellow" style="margin-bottom: 10px;">
                        <span style="font-size: 14px; color: #8D6E63;">🕒 <b>{td['time']}</b></span><br/>
                        <span style="font-size: 20px; font-family: 'Caveat', cursive;">{td['content']}</span>
                    </div>
                    """, unsafe_allow_html=True)

            if "diary_messages" not in st.session_state:
                st.session_state.diary_messages = [
                    {"role": "assistant", "content": f"Merhaba {user_profile['name']}! Bugünü nasıl geçirdin? Sesli konuş veya yaz, günlüğüne ve tracker'larına el yazısıyla işleyeyim!"}
                ]

            if len(st.session_state.diary_messages) > 1:
                with st.expander(f"📜 Geçmiş Sohbet & Notlar ({len(st.session_state.diary_messages)-1} Mesaj)", expanded=False):
                    for msg in st.session_state.diary_messages[:-1]:
                        with st.chat_message(msg["role"]):
                            st.markdown(msg["content"])
                
                # Show only the latest message directly
                latest_msg = st.session_state.diary_messages[-1]
                with st.chat_message(latest_msg["role"]):
                    st.markdown(latest_msg["content"])
            else:
                for msg in st.session_state.diary_messages:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

            # 🎙️ RE-DESIGNED PROMINENT AI VOICE & COMMAND TERMINAL
            st.markdown("""
            <div class="ai-command-card">
                <div class="washi-tape-pink"></div>
                <h3 style="margin-top: 0; color: #5D4037;">🎙️ Deftere Seslen</h3>
            </div>
            """, unsafe_allow_html=True)

            with st.form("bujo_ai_form", clear_on_submit=True):
                chat_text = st.text_input(
                    "Metin Komutu / Günlük Notu:",
                    placeholder="Örn: Bugün harika bir kahve içtim, 1500 ml su içtim ve sinemaya gittim...",
                    key="diary_input_form"
                )
                form_submitted = st.form_submit_button("Deftere İşle 🚀", use_container_width=True)

            # MİKROFON KONTROLÜ (Ortalanmış ve Form Dışında)
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            col_l, col_center, col_r = st.columns([1, 2, 1])
            with col_center:
                audio = mic_recorder(
                    start_prompt="🎙️ Mikrofona Konuş ve Deftere İşle",
                    stop_prompt="⏹️ Kaydı Tamamla & İşle",
                    key='recorder_minimal'
                )

            user_input_text = None
            if audio:
                audio_id = hash(audio['bytes'])
                if st.session_state.get("last_processed_audio_id") != audio_id:
                    st.audio(audio['bytes'], format='audio/wav')
                    with st.spinner("🎤 Sesiniz el yazısına dönüştürülüyor..."):
                        try:
                            audio_filename = "temp_audio.wav"
                            with open(audio_filename, "wb") as f:
                                f.write(audio['bytes'])

                            segments, info = whisper_model.transcribe(
                                audio_filename, 
                                language="tr",
                                initial_prompt="Su içme, kalori, yemek, saatli randevu, film izleme, kitap okuma, günlük olaylar."
                            )
                            user_input_text = " ".join([segment.text for segment in segments]).strip()
                            st.session_state["last_processed_audio_id"] = audio_id

                            if os.path.exists(audio_filename):
                                os.remove(audio_filename)

                        except Exception as e:
                            st.error(f"Ses dönüştürme hatası: {e}")

            final_prompt = user_input_text if user_input_text else (chat_text if form_submitted else None)

            if final_prompt:
                st.session_state.diary_messages.append({"role": "user", "content": final_prompt})
                with st.chat_message("user"):
                    st.markdown(final_prompt)

                with st.chat_message("assistant"):
                    ph = st.empty()
                    ph.markdown("*(Bujo Asistanı analiz ediyor ve deftere işliyor...)*")

                    tracker_prompt = f"""
                    Sen bir Yapay Zeka Destekli Bullet Journal (Bujo) Asistanısın.
                    Kullanıcının cümlesini incele ve SADECE aşağıdaki JSON formatında veri üret:
                    {{
                        "diary_note": "Kullanıcının yaşadığı olayların, gününün özeti (yoksa null)",
                        "water_ml": (Eğer su içtiyse toplam ml hesabı, yoksa 0),
                        "food": (Eğer yemek yediyse [ {{"food_name": "yemek adı", "calories": kalori_tahmini_int}} ], yoksa []),
                        "custom": (Eğer özel takipçiler için bir şey dediyse [ {{"tracker_name": "isim", "value": sayi}} ], yoksa []),
                        "schedule": (Eğer geleceğe dair randevu/plan varsa [ {{"title": "etkinlik adı", "event_date": "YYYY-MM-DD HH:MM"}} ], yoksa []),
                        "media": (Eğer okuduğu/izlediği veya İZLEYECEĞİ/OKUYACAĞI film/kitap/diziden bahsettiyse [ {{"title": "ad", "media_type": "Kitap/Film/Dizi", "creator": "yazar/yönetmen", "rating": 1-5, "review": "yorum", "status": "Tamamlandı veya İstek Listesi"}} ], yoksa []),
                        "stickers": (Eğer metinde kahve, sinema, kitap, yağmur, kedi, mutlu vb. sticker çağrıştıracak kelimeler varsa [ "coffee", "cinema", "happy", "sunny", "cat", "book" ], yoksa []),
                        "response": "Kullanıcıya üslubuna ({user_profile['assistant_style']}) uygun el yazısı tadında yanıt"
                    }}
                    
                    Bugünün Tarihi: {date.today()}
                    Mevcut Özel Takipler: {[ct['name'] for ct in custom_trackers]}
                    SADECE GEÇERLİ JSON DÖNDÜR.
                    """

                    try:
                        res = client.chat.completions.create(
                            model=FOUNDRY_MODEL_ID,
                            messages=[
                                {"role": "system", "content": tracker_prompt},
                                {"role": "user", "content": final_prompt}
                            ]
                        )
                        raw_content = res.choices[0].message.content.strip()
                        if raw_content.startswith("```json"):
                            raw_content = raw_content.replace("```json", "").replace("```", "").strip()

                        parsed = json.loads(raw_content)

                        added_info = []

                        if parsed.get("diary_note"):
                            db.add_diary_entry(parsed["diary_note"])
                            added_info.append("📖 Günlük Notu Deftere Yazıldı")

                        if parsed.get("water_ml", 0) > 0 and modules_status.get("water"):
                            db.add_water(parsed["water_ml"])
                            added_info.append(f"💧 {parsed['water_ml']} ml Su Eklendi")

                        if parsed.get("food") and modules_status.get("calorie"):
                            for f in parsed["food"]:
                                db.add_calorie(f["food_name"], f["calories"])
                                added_info.append(f"🥗 {f['food_name']} ({f['calories']} kcal)")

                        if parsed.get("custom"):
                            for c in parsed["custom"]:
                                for ct in custom_trackers:
                                    if ct["name"].lower() == c["tracker_name"].lower():
                                        db.add_custom_entry(ct["id"], c["value"])
                                        added_info.append(f"✨ {ct['name']}: {c['value']} {ct['unit']}")

                        if parsed.get("schedule") and modules_status.get("schedule"):
                            for s in parsed["schedule"]:
                                db.add_schedule_event(s["title"], s["event_date"], s.get("description", ""))
                                added_info.append(f"📅 Ajanda: {s['title']} ({s['event_date']})")

                        if parsed.get("media") and modules_status.get("media"):
                            for m in parsed["media"]:
                                db.add_or_update_media_entry(
                                    m["title"], m["media_type"], m.get("creator", ""), 
                                    m.get("rating", 0), m.get("review", ""), m.get("status", "Tamamlandı")
                                )
                                st_icon = "📌 İstek" if m.get("status") == "İstek Listesi" else "✅ Tamamlandı"
                                added_info.append(f"🎬 Medya Rafı: {m['title']} ({m['media_type']} - {st_icon})")

                        # OTOMATİK STICKER EKLENTİSİ
                        if parsed.get("stickers"):
                            current_stickers = db.get_stickers_for_date(today_str)
                            for st_key in parsed["stickers"]:
                                cat_found = "cute"
                                for kw, (s_name, s_cat) in STICKER_MAPPING.items():
                                    if s_name == st_key or kw in st_key:
                                        st_key = s_name
                                        cat_found = s_cat
                                        break
                                pos_x = 50 + (len(current_stickers) * 45) % 360
                                pos_y = 60 + (len(current_stickers) // 8) * 60
                                db.add_sticker_entry(today_str, st_key, cat_found, pos_x=pos_x, pos_y=pos_y)
                                added_info.append(f"🎨 Sticker Yapıştırıldı: {st_key}")

                        final_msg = parsed.get("response", "Deftere kaydedildi!")
                        if added_info:
                            final_msg += "\n\n**Deftere İşlenen Kayıtlar:**\n" + "\n".join([f"- {item}" for item in added_info])

                        ph.markdown(final_msg)
                        st.session_state.diary_messages.append({"role": "assistant", "content": final_msg})
                        st.rerun()

                    except Exception as e:
                        ph.error(f"İşlenirken hata oluştu: {repr(e)}")

        # SAĞ SAYFA: HAND-DRAWN MARGIN TRACKERS & TODAY'S SCHEDULE
        with right_col:
            st.markdown("""
            <div class="bujo-paper-card">
                <div class="washi-tape-yellow"></div>
                <h3>📊Takipçiler</h3>
            </div>
            """, unsafe_allow_html=True)

            # 1. BUGÜNÜN ETKİNLİKLERİ VE RANDEVULARI
            today_summary = db.get_day_summary(today_str)
            today_events = today_summary.get("events", [])

            st.markdown("""
            <div class="postit-yellow" style="margin-bottom: 15px;">
                <h4 style="margin: 0; color: #F57F17;">📅 Bugünün Etkinlikleri & Randevuları</h4>
            </div>
            """, unsafe_allow_html=True)

            if today_events:
                for ev in today_events:
                    time_display = ev['event_date'].split(" ")[1] if " " in ev['event_date'] else "12:00"
                    ev_col1, ev_col2 = st.columns([4, 1])
                    with ev_col1:
                        st.info(f"🕒 **{time_display}** — **{ev['title']}**\n\n*{ev.get('description', '') or ''}*")
                    with ev_col2:
                        if st.button("🗑️", key=f"del_today_ev_{ev['id']}"):
                            db.delete_schedule_event(ev['id'])
                            st.rerun()
            else:
                st.caption("Bugün için kayıtlı randevu/etkinlik yok.")

            with st.popover("➕ Bugüne Hızlı Plan Ekle"):
                with st.form("quick_event_form_today", clear_on_submit=True):
                    e_title = st.text_input("Etkinlik Adı", placeholder="Örn: Toplantı veya Dişçi")
                    e_time = st.time_input("Saat")
                    e_desc = st.text_area("Açıklama", placeholder="Açıklama...")
                    if st.form_submit_button("Ajandaya Kaydet 📌") and e_title:
                        full_dt = f"{today_str} {e_time.strftime('%H:%M')}"
                        db.add_schedule_event(e_title, full_dt, e_desc)
                        st.rerun()

            st.divider()

            # 2. SU TAKİBİ
            if modules_status.get("water"):
                water_entries = db.get_today_water_entries()
                total_water = max(0, sum(e['amount_ml'] for e in water_entries))
                target_water = 2500
                w_percent = min(1.0, total_water / target_water)

                st.markdown(f"""
                <div class="postit-blue" style="margin-bottom: 15px;">
                    <h4 style="margin: 0; color: #0277BD;">🥤 Su Takipçisi</h4>
                    <div style="font-size: 24px; font-weight: bold; margin: 6px 0;">{total_water} / {target_water} ml</div>
                </div>
                """, unsafe_allow_html=True)

                st.progress(w_percent)

                w_c1, w_c2 = st.columns(2)
                if w_c1.button("💧 +100 ml", use_container_width=True):
                    db.add_water(100)
                    st.rerun()
                if w_c2.button("🥤 -100 ml", use_container_width=True):
                    if total_water > 0:
                        db.add_water(-100)
                        st.rerun()

            st.divider()

            # 3. KALORİ TAKİBİ
            if modules_status.get("calorie"):
                cal_entries = db.get_today_calorie_entries()
                total_cal = sum(c['calories'] for c in cal_entries)

                st.markdown(f"""
                <div class="postit-green" style="margin-bottom: 15px;">
                    <h4 style="margin: 0; color: #2E7D32;">🥗 Günün Kalori Notu</h4>
                    <div style="font-size: 24px; font-weight: bold; margin: 6px 0;">{total_cal} kcal</div>
                </div>
                """, unsafe_allow_html=True)

                with st.expander("➕ Kalori / Yemek Ekle"):
                    with st.form("quick_cal_form", clear_on_submit=True):
                        fname = st.text_input("Yemek Adı", placeholder="Örn: Elma")
                        fcal = st.number_input("Kalori (kcal)", min_value=10, max_value=2000, value=150)
                        if st.form_submit_button("Logla ✍️") and fname:
                            db.add_calorie(fname, fcal)
                            st.rerun()

            st.divider()

            # 4. ÖZEL TAKİPÇİLER
            if custom_trackers:
                st.markdown("""
                <div class="postit-pink">
                    <h4 style="margin: 0; color: #C2185B;">✨ Özel Habit Matrisi</h4>
                </div>
                """, unsafe_allow_html=True)

                for ct in custom_trackers:
                    c_entries = db.get_today_custom_entries(ct['id'])
                    c_tot = sum(e['value'] for e in c_entries)
                    col_t1, col_t2 = st.columns([2, 1])
                    col_t1.write(f"• **{ct['name']}:** {c_tot} {ct['unit']}")
                    with col_t2:
                        with st.popover("➕"):
                            val_add = st.number_input(f"{ct['unit']}:", min_value=1.0, value=1.0, key=f"pop_ct_{ct['id']}")
                            if st.button("Ekle", key=f"pop_btn_ct_{ct['id']}"):
                                db.add_custom_entry(ct['id'], val_add)
                                st.rerun()

            # 5. ADET DÖNGÜSÜ TAKİBİ (OPSİYONEL)
            if modules_status.get("period"):
                st.divider()
                latest_p = db.get_latest_period_entry()
                st.markdown("""
                <div class="postit-pink" style="margin-bottom: 15px;">
                    <h4 style="margin: 0; color: #C2185B;">🩸 Adet Döngüsü Takipçisi</h4>
                </div>
                """, unsafe_allow_html=True)
                if latest_p:
                    try:
                        s_dt = datetime.strptime(latest_p['start_date'], '%Y-%m-%d').date()
                        days_since = (date.today() - s_dt).days
                        cyc_len = latest_p.get('cycle_length', 28)
                        days_left = max(0, cyc_len - days_since)
                        st.info(f"🌸 Son Başlangıç: **{latest_p['start_date']}** ({days_since}. gün)\n\n⌛ Tahmini Sonraki Döngüye: **{days_left} gün**")
                    except Exception:
                        st.info(f"🌸 Son Kayıt: **{latest_p['start_date']}**")
                else:
                    st.caption("Henüz kayıtlı döngü verisi yok.")

                with st.popover("➕ Yeni Döngü Kaydet"):
                    with st.form("quick_period_form", clear_on_submit=True):
                        p_start = st.date_input("Başlangıç Tarihi", value=date.today())
                        p_len = st.number_input("Ortalama Döngü Süresi (Gün)", value=28, min_value=20, max_value=45)
                        p_notes = st.text_input("Notlar", placeholder="Örn: Sancı, mod vb.")
                        if st.form_submit_button("Döngüyü Kaydet 🩸"):
                            db.add_period_entry(str(p_start), cycle_length=p_len, notes=p_notes)
                            st.success("Döngü kaydedildi!")
                            st.rerun()

    # =========================================================================
    # SAYFA 2: 💬 ÇALIŞMALARIM & SOHBET ODALARI
    # =========================================================================
    elif page == "💬 Çalışmalarım":
        st.markdown("<div class='spiral-ring-bar'></div>", unsafe_allow_html=True)
        st.title("💬 Çalışmalarım & Mürekkep Not Odaları")

        chat_sessions = db.get_all_chat_sessions()
        active_id = st.session_state.get("active_chat_id")

        if not active_id and chat_sessions:
            active_id = chat_sessions[0]["id"]
            st.session_state["active_chat_id"] = active_id

        if active_id:
            current_session = next((s for s in chat_sessions if s["id"] == active_id), None)
            
            if current_session:
                st.markdown(f"""
                <div class="bujo-paper-card">
                    <div class="washi-tape-pink"></div>
                    <h3>📌 Aktif Çalışma Odası: {current_session['title']}</h3>
                </div>
                """, unsafe_allow_html=True)

                messages = db.get_chat_messages(active_id)
                for m in messages:
                    with st.chat_message(m["role"]):
                        st.markdown(m["content"])

                if gen_prompt := st.chat_input("Ders çalışın, beyin fırtınası yapın veya sohbet edin..."):
                    db.add_chat_message(active_id, "user", gen_prompt)
                    
                    system_instr = f"""
                    Sen kullanıcının kişisel akıllı Bullet Journal asistanısın.
                    Kullanıcı: {user_profile['name']}, {user_profile['occupation']}
                    Seçtiğin Üslup kuralı: {user_profile['assistant_style']}
                    Cevap Uzunluğu Kuralı: {user_profile.get('response_length', 'Kısa & Öz')}
                    Kullanıcının Yapay Zeka İçin Koyduğu Özel Kurallar: {user_profile.get('ai_rules', 'Yok')}
                    Hobileri: {', '.join(user_profile['hobbies'])}
                    Hakkında Notlar: {user_profile['about_me']}
                    """

                    try:
                        history = db.get_chat_messages(active_id)
                        api_msgs = [{"role": "system", "content": system_instr}]
                        for h in history:
                            api_msgs.append({"role": h["role"], "content": h["content"]})

                        res = client.chat.completions.create(
                            model=FOUNDRY_MODEL_ID,
                            messages=api_msgs
                        )
                        ai_ans = res.choices[0].message.content
                        db.add_chat_message(active_id, "assistant", ai_ans)
                        st.rerun()

                    except Exception as e:
                        st.error(f"Hata: {e}")
        else:
            st.info("👈 Başlamak için sol menüdeki '➕ Yeni Not Odası' butonuna tıklayın.")

    # =========================================================================
    # SAYFA 3: 📅 AJANDA (MONTHLY LOG & MANTAR PANO)
    # =========================================================================
    elif page == "📅 Ajanda":
        st.markdown("<div class='spiral-ring-bar'></div>", unsafe_allow_html=True)
        st.title("📅 Ajanda & Mantar Pano")

        col_nav1, col_nav2 = st.columns([1, 4])
        with col_nav1:
            today = date.today()
            sel_year = st.number_input("Yıl", value=today.year, min_value=2024, max_value=2030)
            sel_month = st.number_input("Ay", value=today.month, min_value=1, max_value=12)

        month_events = db.get_events_for_month(sel_year, sel_month)
        
        events_by_day = {}
        for ev in month_events:
            try:
                day_num = int(ev['event_date'].split("-")[2].split(" ")[0])
                if day_num not in events_by_day:
                    events_by_day[day_num] = []
                events_by_day[day_num].append(ev)
            except:
                pass

        st.markdown(f"### 🗓️ {calendar.month_name[sel_month]} {sel_year}")
        days_of_week = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
        cols = st.columns(7)
        for idx, day_name in enumerate(days_of_week):
            cols[idx].markdown(f"**{day_name}**")

        cal_matrix = calendar.monthcalendar(sel_year, sel_month)

        if "selected_calendar_date" not in st.session_state:
            st.session_state["selected_calendar_date"] = date.today()

        for week in cal_matrix:
            cols = st.columns(7)
            for idx, day in enumerate(week):
                if day == 0:
                    cols[idx].write("")
                else:
                    day_evs = events_by_day.get(day, [])
                    btn_label = f"📆 {day}"
                    if day_evs:
                        btn_label += f" ({len(day_evs)} Plan)"

                    if cols[idx].button(btn_label, key=f"cal_day_btn_{sel_year}_{sel_month}_{day}", use_container_width=True):
                        st.session_state["selected_calendar_date"] = date(sel_year, sel_month, day)

                    for e in day_evs[:1]:
                        cols[idx].caption(f"📍 {e['title'][:8]}..")

        st.divider()

        # SEÇİLEN GÜNÜN MANTAR PANO (CORKBOARD) DETAYI
        selected_date = st.session_state["selected_calendar_date"]
        
        st.markdown(f"""
        <div class="corkboard-container">
            <h2 style="color: #4E342E; margin: 0 0 15px 0;">📌 Mantar Pano: {selected_date.strftime('%d %B %Y')}</h2>
        </div>
        """, unsafe_allow_html=True)

        summary = db.get_day_summary(str(selected_date))

        c1, c2, c3 = st.columns(3)
        
        # 1. PLANLAR
        with c1:
            st.markdown("""
            <div class="postit-yellow">
                <h4 style="margin:0;">📅 İğnelenmiş Planlar</h4>
            </div>
            """, unsafe_allow_html=True)

            if summary['events']:
                for ev in summary['events']:
                    time_display = ev['event_date'].split(" ")[1] if " " in ev['event_date'] else "12:00"
                    st.info(f"🕒 **{time_display}** — **{ev['title']}**\n\n*{ev.get('description', '') or ''}*")
                    if st.button("🗑️ Sil", key=f"del_ev_btn_{ev['id']}"):
                        db.delete_schedule_event(ev['id'])
                        st.rerun()
            else:
                st.caption("Planlanmış etkinlik yok.")

        # 2. GÜNLÜK NOTLARI
        with c2:
            st.markdown("""
            <div class="postit-green">
                <h4 style="margin:0;">📖 İğnelenmiş Notlar</h4>
            </div>
            """, unsafe_allow_html=True)

            if summary['diaries']:
                for d in summary['diaries']:
                    d_raw = str(d.get('date', ''))
                    if ' ' in d_raw:
                        parts = d_raw.split(' ')
                        d_str = f"🗓️ **{parts[0]}** 🕒 **{parts[1][:5]}**"
                    elif d_raw:
                        d_str = f"🗓️ **{d_raw}**"
                    else:
                        d_str = f"🗓️ **{selected_date.strftime('%Y-%m-%d')}**"

                    st.success(f"{d_str}\n\n{d['content']}")
                    if st.button("🗑️ Notu Sil", key=f"del_diary_btn_{d['id']}"):
                        db.delete_diary_entry(d['id'])
                        st.rerun()
            else:
                st.caption("Günlük notu yok.")

        # 3. SU & KALORİ
        with c3:
            st.markdown("""
            <div class="postit-pink">
                <h4 style="margin:0;">📊 İğnelenmiş Veriler</h4>
            </div>
            """, unsafe_allow_html=True)

            st.write(f"💧 **Su:** {summary['water_ml']} ml")
            tot_cals = sum(c['calories'] for c in summary['calories']) if summary.get('calories') else 0
            st.write(f"🥗 **Kalori:** {tot_cals} kcal")

        st.divider()

        # MANUEL PLAN EKLEME FORMU
        with st.expander(f"➕ ({selected_date.strftime('%d %B %Y')}) Tarihine Plan İğnele"):
            with st.form("add_event_form_selected_day"):
                e_title = st.text_input("Plan / Randevu Başlığı", placeholder="Örn: Dişçi Randevusu")
                e_time = st.time_input("Saat")
                e_desc = st.text_area("Açıklama / Notlar", placeholder="Detaylar...")

                if st.form_submit_button("Panoya İğnele 📌") and e_title:
                    full_date_str = f"{selected_date} {e_time.strftime('%H:%M')}"
                    db.add_schedule_event(e_title, full_date_str, e_desc)
                    st.success(f"{selected_date} tarihine plan eklendi!")
                    st.rerun()

    # =========================================================================
    # SAYFA 4: 📚 OKUMA & İZLEME RAFI (WOODEN BOOKSHELF & CINEMA TICKETS)
    # =========================================================================
    elif page == "📚 Okuma & İzleme Rafı":
        st.markdown("<div class='spiral-ring-bar'></div>", unsafe_allow_html=True)
        st.title("📚 Kitap, Film & Dizi Rafım")


        all_media = db.get_all_media()

        with st.expander("➕ Ahşap Rafa Yeni Eser Koy"):
            with st.form("manual_media_form", clear_on_submit=True):
                m_title = st.text_input("Eser Adı", placeholder="")
                m_type = st.selectbox("Tür", ["Film", "Dizi", "Kitap"])
                m_status = st.selectbox("Durumu", ["Tamamlandı", "İstek Listesi"])
                m_creator = st.text_input("Yazar / Yönetmen", placeholder="")
                m_rating = st.slider("Puanın", 0, 5, 5 if m_status=="Tamamlandı" else 0)
                m_review = st.text_area("Yorumun", placeholder="Düşünceleriniz...")

                if st.form_submit_button("Rafa Yerleştir 🪵"):
                    if m_title.strip():
                        db.add_or_update_media_entry(m_title, m_type, m_creator, m_rating, m_review, m_status)
                        st.success("Rafa eklendi!")
                        st.rerun()

        st.divider()

        type_f = st.session_state.get("media_type_filter", "Tümü")
        status_f = st.session_state.get("media_status_filter", "Hepsi")

        filtered_media = all_media
        if "Film" in type_f:
            filtered_media = [m for m in filtered_media if m["media_type"] == "Film"]
        elif "Dizi" in type_f:
            filtered_media = [m for m in filtered_media if m["media_type"] == "Dizi"]
        elif "Kitap" in type_f:
            filtered_media = [m for m in filtered_media if m["media_type"] == "Kitap"]

        if "Tamamlananlar" in status_f:
            filtered_media = [m for m in filtered_media if m["status"] == "Tamamlandı"]
        elif "İstek Listesi" in status_f:
            filtered_media = [m for m in filtered_media if m["status"] == "İstek Listesi"]

        if not filtered_media:
            st.info("Ahşap rafta gösterilecek eser bulunamadı.")
        else:
            st.markdown("<div class='bujo-bookshelf'>", unsafe_allow_html=True)
            chunks = [filtered_media[i:i+3] for i in range(0, len(filtered_media), 3)]
            for chunk_idx, chunk in enumerate(chunks):
                cols = st.columns(3)
                for c_idx, item in enumerate(chunk):
                    with cols[c_idx]:
                        if item["media_type"] == "Kitap":
                            st.markdown(f"""
                            <div class="book-cover-3d">
                                <div class="book-ribbon"></div>
                                <div style="font-size: 12px; letter-spacing: 2px; color: #FFE082;">📖 BOOK COVER</div>
                                <h3 style="margin: 4px 0; color: #FFF8E1;">{item['title']}</h3>
                                <p style="margin: 0; font-size: 14px; color: #FFE082;">✍️ {item['creator'] or 'Yazar Bilinmiyor'} | {'⭐' * item['rating']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div class="cinema-ticket">
                                <div style="font-size: 12px; letter-spacing: 2px;">🎟️ CINEMA TICKET</div>
                                <h3 style="margin: 4px 0; color: white;">{item['title']}</h3>
                                <p style="margin: 0; font-size: 14px;">🎬 {item['creator'] or 'Yönetmen Bilinmiyor'} | {'⭐' * item['rating']}</p>
                            </div>
                            """, unsafe_allow_html=True)

                        if item["review"]:
                            st.caption(f"*{item['review']}*")

                        c_b1, c_b2 = st.columns(2)
                        with c_b1:
                            with st.popover("✏️ Düzenle"):
                                e_title = st.text_input("Eser Adı", value=item["title"], key=f"med_t_{item['id']}")
                                curr_st_idx = 0 if item['status'] == "Tamamlandı" else 1
                                e_status = st.selectbox("Durumu", ["Tamamlandı", "İstek Listesi"], index=curr_st_idx, key=f"med_st_{item['id']}")
                                e_rating = st.slider("Puan", 0, 5, item["rating"], key=f"med_rt_{item['id']}")
                                e_review = st.text_area("Yorum", value=item["review"] or "", key=f"med_rv_{item['id']}")
                                if st.button("Kaydet", key=f"save_med_{item['id']}"):
                                    db.update_media_entry(item['id'], e_title, item['media_type'], item['creator'], e_rating, e_review, e_status)
                                    st.rerun()
                        with c_b2:
                            if st.button("🗑️ Sil", key=f"del_med_{item['id']}"):
                                db.delete_media_entry(item['id'])
                                st.rerun()

                # Physical Wooden Bookshelf Plank under each 3-item row
                st.markdown("<div class='wooden-shelf-bar'></div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================================
    # SAYFA 5: ⚙️ DEFTER AYARLARI & İNDEKS
    # =========================================================================
    elif page == "⚙️ Defter Ayarları & İndeks":
        st.markdown("<div class='spiral-ring-bar'></div>", unsafe_allow_html=True)
        st.title("⚙️ Defter Kapağı & Kişisel Ayarlar")

        tab_prof, tab_ai, tab_mods, tab_stickers = st.tabs([
            "👤 Profil & Defter Sahibi", 
            "🧠 Bujo Asistan Mizaç & Kurallar", 
            "🧩 Tracker Modülleri",
            "🎨 Sticker & Süsleme Yönetimi"
        ])

        with tab_prof:
            with st.form("update_profile_form"):
                st.subheader("📌 Temel Bilgiler")
                col1, col2 = st.columns(2)
                with col1:
                    u_name = st.text_input("Ad Soyad", value=user_profile.get("name", ""))
                    g_options = ["Erkek", "Kadın", "Belirtmek İstemiyorum"]
                    curr_g = user_profile.get("gender", "Belirtmek İstemiyorum")
                    g_idx = g_options.index(curr_g) if curr_g in g_options else 2
                    u_gender = st.selectbox("Cinsiyet", options=g_options, index=g_idx)
                    u_occupation = st.text_input("Meslek / Okul", value=user_profile.get("occupation", ""))

                with col2:
                    u_height = st.number_input("Boy (cm)", value=float(user_profile.get("height", 175)))
                    u_weight = st.number_input("Kilo (kg)", value=float(user_profile.get("weight", 70)))

                st.divider()
                raw_hobbies = user_profile.get("hobbies", [])
                if isinstance(raw_hobbies, str):
                    try:
                        curr_hobbies = json.loads(raw_hobbies)
                    except Exception:
                        curr_hobbies = [h.strip() for h in raw_hobbies.split(",") if h.strip()]
                elif isinstance(raw_hobbies, list):
                    curr_hobbies = raw_hobbies
                else:
                    curr_hobbies = []

                # Hobiler opsiyon listesinde yoksa (ör. 'Fotoğrafçılık'), Streamlit hatasını önlemek için opsiyonlara ekle
                all_hobby_options = list(dict.fromkeys(HOBBY_OPTIONS + [str(h) for h in curr_hobbies if h]))
                u_hobbies = st.multiselect("Hobilerin:", options=all_hobby_options, default=curr_hobbies)
                u_about = st.text_area("Hakkımda Özel Notlar:", value=user_profile.get("about_me", ""))

                if st.form_submit_button("Profil Bilgilerini Deftere Kaydet 💾"):
                    updated_data = {
                        "name": u_name,
                        "gender": u_gender,
                        "birth_date": user_profile.get("birth_date"),
                        "height": u_height,
                        "weight": u_weight,
                        "occupation": u_occupation,
                        "hobbies": u_hobbies,
                        "about_me": u_about,
                        "assistant_style": user_profile.get("assistant_style", ASSISTANT_STYLES[0]),
                        "response_length": user_profile.get("response_length", RESPONSE_LENGTHS[0]),
                        "ai_rules": user_profile.get("ai_rules", "")
                    }
                    db.save_profile_db(updated_data)
                    st.success("Profil güncellendi!")
                    st.rerun()

        with tab_ai:
            st.subheader("🧠 Yapay Zeka Mizaç Ayarları")
            with st.form("ai_training_form"):
                curr_style_idx = 0
                for idx, s in enumerate(ASSISTANT_STYLES):
                    if user_profile.get("assistant_style", "") in s:
                        curr_style_idx = idx
                        break
                u_style = st.selectbox("Asistan Kişiliği:", options=ASSISTANT_STYLES, index=curr_style_idx)
                
                curr_len = user_profile.get("response_length", "")
                len_idx = RESPONSE_LENGTHS.index(curr_len) if curr_len in RESPONSE_LENGTHS else 0
                u_len = st.selectbox("Cevap Uzunluğu:", options=RESPONSE_LENGTHS, index=len_idx)
                u_rules = st.text_area("Yapay Zekaya Özel Kurallar (Prompt):", value=user_profile.get("ai_rules", ""))

                if st.form_submit_button("Bujo Mizaç Ayarlarını Kaydet 🧠"):
                    updated_data = {
                        "name": user_profile.get("name"),
                        "gender": user_profile.get("gender"),
                        "birth_date": user_profile.get("birth_date"),
                        "height": user_profile.get("height"),
                        "weight": user_profile.get("weight"),
                        "occupation": user_profile.get("occupation"),
                        "hobbies": user_profile.get("hobbies"),
                        "about_me": user_profile.get("about_me"),
                        "assistant_style": u_style,
                        "response_length": u_len,
                        "ai_rules": u_rules
                    }
                    db.save_profile_db(updated_data)
                    st.success("Bujo mizaç ayarları güncellendi!")
                    st.rerun()

        with tab_mods:
            st.subheader("🎛️ Modül Toggles & Özel Habit Takipçileri")
            c_water = st.checkbox("💧 Su Takibi", value=modules_status.get("water", True))
            c_cal = st.checkbox("🥗 Kalori Takibi", value=modules_status.get("calorie", True))
            c_sched = st.checkbox("📅 Ajanda", value=modules_status.get("schedule", True))
            c_media = st.checkbox("📚 Okuma & İzleme Rafı", value=modules_status.get("media", True))
            c_period = st.checkbox("🩸 Adet Döngüsü Takibi (Opsiyonel)", value=modules_status.get("period", False))

            if (c_water != modules_status.get("water") or 
                c_cal != modules_status.get("calorie") or 
                c_sched != modules_status.get("schedule") or 
                c_media != modules_status.get("media") or
                c_period != modules_status.get("period")):
                db.set_module_status("water", c_water)
                db.set_module_status("calorie", c_cal)
                db.set_module_status("schedule", c_sched)
                db.set_module_status("media", c_media)
                db.set_module_status("period", c_period)
                st.success("Modüller güncellendi!")
                st.rerun()

            st.divider()
            st.subheader("✨ Yeni Özel Habit Ekle")
            with st.form("new_custom_tracker_form"):
                ct_name = st.text_input("Takip Başlığı", placeholder="Örn: Uyku, Kahve")
                ct_unit = st.text_input("Birim", placeholder="Örn: Saat, Bardak")
                if st.form_submit_button("Ekle ➕") and ct_name and ct_unit:
                    res = db.add_custom_tracker(ct_name, ct_unit)
                    if res:
                        st.success(f"'{ct_name}' takipçisi eklendi!")
                        st.rerun()

        with tab_stickers:
            st.subheader("🎨 Özel SVG Sticker Yükle & Koleksiyon Yönetimi")
            st.caption("Kendi SVG sticker dosyalarınızı yükleyerek defter yaprağınızda kullanabilirsiniz.")

            with st.form("upload_sticker_form"):
                uploaded_svg = st.file_uploader("SVG Sticker Dosyası Yükleyin", type=["svg"])
                cat_choices = ["cute", "mood", "weather", "food", "tapes", "➕ Yeni Kategori"]
                selected_cat_opt = st.selectbox("Kategori Seçin:", options=cat_choices)
                
                custom_cat_name = ""
                if selected_cat_opt == "➕ Yeni Kategori":
                    custom_cat_name = st.text_input("Yeni Kategori İsmi (küçük harf):", placeholder="örn: hobbies")

                sticker_file_key = st.text_input("Sticker İsmi / Anahtar Kelime:", placeholder="Örn: star_pink")
                
                if st.form_submit_button("Sticker'ı Koleksiyona Ekle 📥"):
                    if uploaded_svg and sticker_file_key.strip():
                        target_cat = custom_cat_name.strip().lower() if selected_cat_opt == "➕ Yeni Kategori" else selected_cat_opt
                        if target_cat:
                            cat_folder = os.path.join(canvas_comp.STICKER_DIR, target_cat)
                            os.makedirs(cat_folder, exist_ok=True)
                            
                            safe_key = "".join([c for c in sticker_file_key.strip() if c.isalnum() or c in ('_', '-')])
                            svg_path = os.path.join(cat_folder, f"{safe_key}.svg")
                            
                            with open(svg_path, "wb") as f:
                                f.write(uploaded_svg.read())
                            
                            st.success(f"🎨 '{safe_key}.svg' sticker'ı '{target_cat}' kategorisine başarıyla kaydedildi!")
                            st.rerun()
                        else:
                            st.error("Lütfen geçerli bir kategori ismi girin.")
                    else:
                        st.warning("Lütfen hem bir SVG dosyası hem de sticker ismi girin.")

            st.divider()
            st.markdown("### 📚 Mevcut SVG Sticker Koleksiyonu")
            
            all_svgs = canvas_comp.load_all_svg_stickers()
            if all_svgs:
                for c_name, c_items in all_svgs.items():
                    with st.expander(f"📁 Kategori: {c_name} ({len(c_items)} sticker)"):
                        i_cols = st.columns(6)
                        for idx, (s_key, s_uri) in enumerate(c_items.items()):
                            c_idx = idx % 6
                            with i_cols[c_idx]:
                                st.image(s_uri, width=50)
                                st.caption(s_key)
                                if st.button("🗑️", key=f"del_svg_{c_name}_{s_key}"):
                                    f_to_del = os.path.join(canvas_comp.STICKER_DIR, c_name, f"{s_key}.svg")
                                    if os.path.exists(f_to_del):
                                        os.remove(f_to_del)
                                        st.success(f"'{s_key}' silindi.")
                                        st.rerun()
            else:
                st.caption("Henüz yüklenmiş SVG sticker yok.")