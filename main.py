import subprocess
import time
import sys
import os
import webview

def start_app():
    # Mevcut çalışma dizinini al
    base_path = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(base_path, "app.py")
    icon_path = os.path.join(base_path, "assets", "bujo_icon.ico")

    # Streamlit sunucusunu arka planda gizlice başlat
    # --server.headless=true tarayıcının otomatik açılmasını engeller
    cmd = [
        sys.executable, "-m", "streamlit", "run", app_path,
        "--server.headless=true",
        "--server.port=8501",
        "--global.developmentMode=false"
    ]
    
    # Arka plan süreci
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Streamlit'in ayağa kalkması için kısa bir süre bekle
    time.sleep(2.5)

    # Özel Masaüstü Penceresini Oluştur (Full Windowed / Maximized)
    window = webview.create_window(
        title="Bujo",
        url="http://localhost:8501",
        width=1350,
        height=850,
        resizable=True,
        maximized=True,
        min_size=(900, 600)
    )

    # Pencere kapatıldığında arka plandaki Streamlit sürecini de sonlandır
    def on_closed():
        process.kill()

    window.events.closed += on_closed
    webview.start(icon=icon_path if os.path.exists(icon_path) else None)

if __name__ == "__main__":
    start_app()
