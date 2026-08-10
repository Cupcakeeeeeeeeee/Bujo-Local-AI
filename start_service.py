from foundry_local_sdk import Configuration, FoundryLocalManager
import time
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

class DownloadProgressBar:
    """
    Terminalde alt alta yüzlerce satır basmak yerine tek bir satırda
    modern ve temiz bir ilerleme çubuğu ([██████░░░░] %60) gösterir.
    """
    def __init__(self, label="İndiriliyor"):
        self.label = label
        self.last_pct = -1

    def __call__(self, *args):
        if len(args) == 2:
            extra = f"({args[0]})"
            pct = args[1]
        elif len(args) == 1:
            extra = ""
            pct = args[0]
        else:
            return

        current_pct = int(pct)
        if current_pct == self.last_pct:
            return
        self.last_pct = current_pct

        bar_length = 25
        filled_length = int(bar_length * current_pct // 100)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        prefix = f" {self.label} {extra}".rstrip()
        sys.stdout.write(f"\r{prefix}: [{bar}] %{current_pct:3d}")
        sys.stdout.flush()
        if current_pct >= 100:
            sys.stdout.write("\n")
            sys.stdout.flush()

MODEL_ALIAS = "phi-4-mini"
INFO_FILE = "foundry_service_info.json"   # app.py ile aynı klasörde olsun

config = Configuration(app_name="kisisel_asistan_service")   # port belirtmiyoruz, dinamik kalsın
FoundryLocalManager.initialize(config)
manager = FoundryLocalManager.instance

print("⚙️ Execution provider'lar hazırlanıyor...")
try:
    manager.download_and_register_eps(progress_callback=DownloadProgressBar("⚙️ EP"))
except Exception as ep_err:
    print(f"⚠️ EP yükleme uyarısı: {ep_err}")

model = manager.catalog.get_model(MODEL_ALIAS)

def load_best_model_variant(model):
    """
    Kullanıcının donanımında varsayılan EP (örneğin OpenVINO) yüklü veya uyumlu değilse,
    CUDA, Generic GPU veya CPU varyantlarına otomatik geçiş yaparak çökmesini engeller.
    """
    print(f"📦 Model hazırlanıyor: {model.id}")
    try:
        model.download(DownloadProgressBar("📥 İndiriliyor"))
        model.load()
        print(f"✅ Model varyantı başarıyla yüklendi: {model.id}")
        return True
    except Exception as err:
        print(f"\n⚠️ Varsayılan model varyantı ({model.id}) yüklenemedi: {err}")
        print("🔄 Donanımınızla uyumlu alternatif varyantlar taranıyor...")

    # Varyantları sırala: CUDA / GPU varyantları önce, Generic CPU en son çare (her bilgisayarda çalışır)
    variants = list(model.variants)
    
    def variant_priority(v):
        v_id = v.id.lower()
        if "cuda" in v_id:
            return 1
        elif "gpu" in v_id and "openvino" not in v_id:
            return 2
        elif "cpu" in v_id:
            return 3
        return 4

    sorted_variants = sorted(variants, key=variant_priority)

    for variant in sorted_variants:
        if variant.id == model.id:
            continue
        try:
            print(f"👉 Deneniyor: {variant.id}")
            model.select_variant(variant)
            model.download(DownloadProgressBar("📥 İndiriliyor"))
            model.load()
            print(f"✅ Uyumlu model varyantı yüklendi: {variant.id}")
            return True
        except Exception as v_err:
            print(f"\n ❌ {variant.id} yüklenemedi: {v_err}")

    return False

if not load_best_model_variant(model):
    print("❌ HATA: Hiçbir model varyantı donanımınızda yüklenemedi!")
    sys.exit(1)

manager.start_web_service()
base_url = f"{manager.urls[0]}/v1"

# Gerçek port ve model id'yi dosyaya yaz
with open(INFO_FILE, "w") as f:
    json.dump({"base_url": base_url, "model_id": model.id}, f)

print(f"✅ Servis hazır: {base_url}")
print(f"Bilgiler '{INFO_FILE}' dosyasına yazıldı.")

while True:
    time.sleep(3600)