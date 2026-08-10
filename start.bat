@echo off
title Bujo - Local AI Assistant Launcher

echo ===================================================
echo   Bujo - Yerel Yapay Zeka Destekli Asistan
echo ===================================================
echo.

if not exist "venv" (
    echo [1/3] Sanal ortam ^(venv^) bulunamadi, otomatik olusturuluyor...
    python -m venv venv
    if errorlevel 1 (
        echo.
        echo [HATA] Python bulunamadi! Lutfen bilgisayarinizda Python 3.10 veya uzeri kurulu oldugundan emin olun.
        echo Download: https://www.python.org/downloads/
        echo.
        pause
        exit /b 1
    )
    echo [OK] Sanal ortam basariyla olusturuldu.
)

echo [2/3] Gerekli kutuphaneler denetleniyor ve yukleniyor...
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet
echo [OK] Kutuphaneler hazir.

echo [3/3] Bujo Asistan baslatiliyor...
echo.
python run.py

if errorlevel 1 (
    echo.
    echo [HATA] Uygulama calisirken bir sorun olustu.
    pause
)
