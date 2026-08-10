import os
import sys
import time
import subprocess
import signal

def run_app():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    service_script = os.path.join(base_dir, "start_service.py")
    main_script = os.path.join(base_dir, "main.py")
    info_file = os.path.join(base_dir, "foundry_service_info.json")

    # 1. Eski servis bilgi dosyasını temizle (varsa)
    if os.path.exists(info_file):
        try:
            os.remove(info_file)
        except Exception:
            pass

    print("🚀 [1/2] Yerel AI Servisi (start_service.py) başlatılıyor...")
    service_process = subprocess.Popen([sys.executable, service_script])

    # 2. Servisin hazır olmasını ve foundry_service_info.json oluşmasını bekle
    print("⏳ Servisin ayağa kalkması ve modelin hazırlanması bekleniyor...")
    max_wait = 300  # 5 dakika maksimum bekleme süresi
    start_time = time.time()
    
    while True:
        if os.path.exists(info_file) and os.path.getsize(info_file) > 0:
            print("✅ Yerel AI Servisi başarıyla hazırlandı!")
            break
        
        # Servis beklenmedik şekilde kapandı mı kontrol et
        if service_process.poll() is not None:
            print("❌ HATA: start_service.py beklenmedik bir şekilde kapandı.")
            sys.exit(1)

        if time.time() - start_time > max_wait:
            print("❌ HATA: Servis başlatma zaman aşımına uğradı.")
            service_process.terminate()
            sys.exit(1)

        time.sleep(1.5)

    # 3. Masaüstü arayüzünü (main.py) başlat
    print("🎨 [2/2] Bujo Masaüstü Arayüzü açılıyor...")
    try:
        main_process = subprocess.run([sys.executable, main_script])
    except KeyboardInterrupt:
        print("\n🛑 Kullanıcı tarafından durduruldu.")
    finally:
        # 4. Arayüz kapatıldığında arka plandaki AI servisini temizle
        print("🧹 Arka plan AI servisi sonlandırılıyor...")
        service_process.terminate()
        try:
            service_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            service_process.kill()
        print("👋 Bujo başarıyla kapatıldı.")

if __name__ == "__main__":
    run_app()
