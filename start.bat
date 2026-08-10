@echo off
title Bujo - Local AI Assistant Launcher
chcp 65001 > nul
echo ===================================================
echo   Bujo - Yerel Yapay Zeka Destekli Asistan
echo ===================================================
echo.

:: 1. Sanal ortam (venv) kontrolü
if not exist "venv" (
    echo ⚙️ [1/3] Sanal ortam (venv) bulunamadı, otomatik oluşturuluyor...
    python -m venv venv
    if errorlevel 1 (
        echo.
        echo ❌ [HATA] Python bulunamadı! Lütfen bilgisayarınızda Python 3.10 veya üzeri kurulu olduğundan emin olun.
        echo Download: https://www.python.org/downloads/
        echo.
        pause
        exit /b 1
    )
    echo ✅ Sanal ortam başarıyla oluşturuldu.
)

:: 2. Bağımlılıkların yüklenmesi
echo 📦 [2/3] Gerekli kütüphaneler denetleniyor ve yükleniyor...
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet
echo ✅ Kütüphaneler hazır.

:: 3. Uygulamanın başlatılması
echo 🚀 [3/3] Bujo Asistan başlatılıyor...
echo.
python run.py

if errorlevel 1 (
    echo.
    echo ❌ Uygulama çalışırken bir sorun oluştu.
    pause
)
