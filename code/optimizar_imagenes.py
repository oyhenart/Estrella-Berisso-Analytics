"""
optimizar_imagenes.py
======================
Reduce el peso de las fotos de jugadores y escudos para que el dashboard
cargue rápido en celular. No modifica los originales: crea copias optimizadas.

CÓMO USARLO (desde la carpeta code/, en GitHub Codespaces o local):

    python optimizar_imagenes.py

Esto va a:
  1. Leer todo lo que hay en static/fotos/ y static/escudos/
  2. Redimensionar cada imagen (manteniendo proporción) a un tamaño máximo
  3. Comprimir y guardar en formato WebP (mucho más liviano que JPG/PNG)
  4. Guardar las versiones optimizadas en static/fotos_opt/ y static/escudos_opt/
     SIN tocar tus carpetas originales (por si algo sale mal, no perdés nada)

Después de correrlo y revisar que las fotos se vean bien, hay 2 caminos:
  A) Reemplazar las carpetas originales por las optimizadas (recomendado)
  B) Apuntar el código a las nuevas carpetas _opt (más conservador)

Te indico abajo cómo hacer el reemplazo (paso 2 de las instrucciones).
"""

import os
from PIL import Image

# ==========================
# CONFIGURACIÓN
# ==========================
BASE = os.path.dirname(os.path.abspath(__file__))

# Carpeta : (tamaño máximo en px, calidad WebP 1-100)
CARPETAS = {
    os.path.join(BASE, "static", "fotos"):   {"max_size": 500, "calidad": 80, "salida": "fotos_opt"},
    os.path.join(BASE, "static", "escudos"): {"max_size": 200, "calidad": 85, "salida": "escudos_opt"},
}

EXTENSIONES_VALIDAS = (".jpg", ".jpeg", ".png", ".webp", ".bmp")


def optimizar_carpeta(carpeta_origen: str, max_size: int, calidad: int, nombre_salida: str):
    if not os.path.isdir(carpeta_origen):
        print(f"⚠️  No existe: {carpeta_origen} (la salto)")
        return

    carpeta_destino = os.path.join(os.path.dirname(carpeta_origen), nombre_salida)
    os.makedirs(carpeta_destino, exist_ok=True)

    archivos = [f for f in os.listdir(carpeta_origen) if f.lower().endswith(EXTENSIONES_VALIDAS)]
    if not archivos:
        print(f"ℹ️  Sin imágenes en {carpeta_origen}")
        return

    peso_antes_total = 0
    peso_despues_total = 0

    print(f"\n📁 Procesando: {carpeta_origen}  ({len(archivos)} archivos)")

    for nombre_archivo in archivos:
        ruta_in = os.path.join(carpeta_origen, nombre_archivo)
        nombre_base = os.path.splitext(nombre_archivo)[0]
        ruta_out = os.path.join(carpeta_destino, f"{nombre_base}.webp")

        peso_antes = os.path.getsize(ruta_in)
        peso_antes_total += peso_antes

        try:
            with Image.open(ruta_in) as img:
                # Convertir a RGB si tiene canal alfa raro o es modo P (paleta)
                if img.mode in ("P", "RGBA"):
                    img = img.convert("RGB")

                # Redimensionar manteniendo proporción, solo si es más grande que el máximo
                img.thumbnail((max_size, max_size), Image.LANCZOS)

                img.save(ruta_out, "WEBP", quality=calidad, method=6)

            peso_despues = os.path.getsize(ruta_out)
            peso_despues_total += peso_despues
            reduccion = round((1 - peso_despues / peso_antes) * 100) if peso_antes > 0 else 0
            print(f"   {nombre_archivo:30s} {peso_antes/1024:6.0f} KB → {peso_despues/1024:6.0f} KB  (-{reduccion}%)")

        except Exception as e:
            print(f"   ❌ Error con {nombre_archivo}: {e}")

    if peso_antes_total > 0:
        reduccion_total = round((1 - peso_despues_total / peso_antes_total) * 100)
        print(f"   ──────────────────────────────────────────")
        print(f"   TOTAL: {peso_antes_total/1024:.0f} KB → {peso_despues_total/1024:.0f} KB  (-{reduccion_total}%)")
        print(f"   Guardado en: {carpeta_destino}")


def main():
    print("=" * 60)
    print(" OPTIMIZADOR DE IMÁGENES — Estrella FC Dashboard")
    print("=" * 60)

    for carpeta, cfg in CARPETAS.items():
        optimizar_carpeta(carpeta, cfg["max_size"], cfg["calidad"], cfg["salida"])

    print("\n✅ Listo. Revisá las carpetas *_opt para confirmar que las fotos se ven bien.")
    print("   Cuando estés conforme, seguí el paso 2 de las instrucciones para")
    print("   reemplazar las carpetas originales (o avisame y lo hago por vos).")


if __name__ == "__main__":
    main()
