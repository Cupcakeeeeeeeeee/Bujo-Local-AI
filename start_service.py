from foundry_local_sdk import Configuration, FoundryLocalManager
import time, json

MODEL_ALIAS = "phi-4-mini"
INFO_FILE = "foundry_service_info.json"   # app.py ile aynı klasörde olsun

config = Configuration(app_name="kisisel_asistan_service")   # port belirtmiyoruz, dinamik kalsın
FoundryLocalManager.initialize(config)
manager = FoundryLocalManager.instance

print("Execution provider'lar hazırlanıyor...")
manager.download_and_register_eps(progress_callback=lambda ep, pct: print(f"{ep}: %{pct:.0f}"))

model = manager.catalog.get_model(MODEL_ALIAS)
model.download(lambda pct: print(f"İndirme: %{pct:.0f}"))
model.load()

manager.start_web_service()
base_url = f"{manager.urls[0]}/v1"

# Gerçek port ve model id'yi dosyaya yaz
with open(INFO_FILE, "w") as f:
    json.dump({"base_url": base_url, "model_id": model.id}, f)

print(f"✅ Servis hazır: {base_url}")
print(f"Bilgiler '{INFO_FILE}' dosyasına yazıldı.")

while True:
    time.sleep(3600)