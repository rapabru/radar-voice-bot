import zipfile
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

zip_name = 'bot.zip'
files_to_include = ['main.py', 'config.py', 'discloud.config', 'requirements.txt', '.env']
dirs_to_include = ['cogs']

print(f"📦 Empaquetando bot en '{zip_name}'...")
with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for f in files_to_include:
        if os.path.exists(f):
            zipf.write(f, arcname=f)
            print(f"  + {f}")
    for d in dirs_to_include:
        for root, dirs, files in os.walk(d):
            if '__pycache__' in root:
                continue
            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    arc_path = os.path.relpath(full_path, '.')
                    zipf.write(full_path, arcname=arc_path)
                    print(f"  + {arc_path}")

print(f"\n✅ Archivo '{zip_name}' generado con éxito. Listo para subir a Discloud.")
