# ✍️ Bujo - Yerel Yapay Zeka Destekli Kişisel Asistan & Günlük

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)
![Streamlit](https://img.shields.io/badge/UI-Streamlit%20%2B%20PyWebView-red.svg)
![AI Model](https://img.shields.io/badge/AI-Foundry%20Local%20SDK%20(Phi--4--mini)-orange.svg)

**Bujo**, tamamen yerel cihazınızda çalışan (Local LLM), gizlilik odaklı kişisel asistan, Bullet Journal ve not tutma uygulamasıdır. İnternet bağlantısına veya üçüncü taraf bulut servislerine ihtiyaç duymadan, kendi bilgisayarınızın gücüyle çalışan akıllı bir yardımcı sunar.

---

## ✨ Özellikler

- 🔒 **%100 Yerel ve Gizli:** Tüm sohbetler, notlar ve profil bilgileri yerel SQLite veritabanınızda tutulur. Dış sunuculara veri aktarılmaz.
- 🤖 **Güçlü Yerel AI (Phi-4-mini):** `foundry-local-sdk` altyapısı ile donanımınıza uygun execution provider (OpenVINO / GPU / DirectML / CPU) otomatik yapılandırılır.
- 🖥️ **Masaüstü Uygulama Deneyimi:** Streamlit esnekliği `PyWebView` ile harmanlanarak bağımsız bir masaüstü penceresi olarak sunulur.
- 🎙️ **Sesli Asistan (Faster-Whisper):** Ses kayıtlarınızı doğrudan yerel cihazınızda yüksek doğrulukla metne çevirir.
- 📅 **Bullet Journal & Planlayıcı:** Günlük yapılacaklar listesi, takvim görünümleri ve kişiselleştirilebilir not alanı.
- 🎨 **Yapışkan Notlar & Etiket Canvas:** Sürükleyip bırakılabilir veya özelleştirilebilir interaktif dijital kanvas bileşeni.

---

---

## 🚀 Çalıştırma ve Kurulum Seçenekleri

### 🟢 Seçenek A: Tek Tıkla Kurulum & Çalıştırma (Kod Bilmeyen Kullanıcılar İçin)

Projeyi indirdikten sonra klasör içerisindeki **`start.bat`** dosyasına **çift tıklamanız yeterlidir**. 

`start.bat` betiği otomatik olarak:
1. Sanal ortamı (`venv`) oluşturur.
2. Gerekli tüm Python kütüphanelerini yükler.
3. Yerel AI servisini ve masaüstü arayüzünü tek tıkla başlatır.

---

### 🔵 Seçenek B: Manuel Kurulum & Çalıştırma (Geliştiriciler İçin)

#### 1. Depoyu Klonlayın
```bash
git clone https://github.com/Cupcakeeeeeeeeee/Bujo-Local-AI.git
cd Bujo-Local-AI
```

#### 2. Sanal Ortam Oluşturun ve Bağımlılıkları Yükleyin
```bash
# Windows (PowerShell)
python -m venv venv

# PowerShell script çalıştırma izni hatası alırsanız önce şu komutu çalıştırın:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Sanal ortamı aktifleştirin:
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Paketleri Yükleyin
pip install -r requirements.txt
```

#### 3. Çalıştırın
```bash
python run.py
```
*(Veya iki farklı terminalde `python start_service.py` ve `python main.py` çalıştırabilirsiniz).*

---

## 📂 Proje Yapısı

```text
.
├── assets/                  # İkonlar, stiller ve görsel varlıklar
├── components/              # Özel Streamlit & Canvas bileşenleri
├── database/                # SQLite veritabanı yönetimi (db_manager.py)
├── .streamlit/              # Streamlit tema ve sunucu konfigürasyonu
├── app.py                   # Streamlit ana arayüzü ve sayfa mantığı
├── main.py                  # PyWebView masaüstü pencere başlatıcısı
├── start_service.py         # Foundry Local SDK yerel model servisi
├── run.py                   # Tek komutla orkestrasyon betiği
├── requirements.txt         # Python bağımlılıkları
├── user_profile.json.example# Örnek kullanıcı profil şablonu
├── .gitignore               # Gizlenecek yerel ve geçici dosyalar
└── README.md                # Proje dokümantasyonu
```

---

## 📜 Lisans

Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır. Dilediğiniz gibi geliştirebilir, özelleştirebilir ve kullanabilirsiniz.
