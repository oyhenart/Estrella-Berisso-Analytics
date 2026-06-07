"""
procesar_partido.py
-------------------
Uso:
    python procesar_partido.py --pt primer_tiempo.csv --st segundo_tiempo.csv --fecha 2 --dir_pt izq --dir_st der

Argumentos:
    --pt        CSV del primer tiempo (requerido)
    --st        CSV del segundo tiempo (requerido)
    --fecha     Número de fecha del torneo (requerido)
    --dir_pt    Dirección de ataque en el primer tiempo: 'izq' (izq→der) o 'der' (der→izq). Default: izq
    --dir_st    Dirección de ataque en el segundo tiempo: 'izq' o 'der'. Default: der
    --output    Ruta al events_clean.csv. Default: data/events_clean.csv
    --equipo    Nombre del equipo en el CSV. Default: Estrella
"""

import pandas as pd
import argparse
import os

def parsear_mitad(filepath, mitad, fecha, espejo, equipo):
    df = pd.read_csv(filepath)
    rows = []
    i = 0
    while i < len(df):
        row = df.iloc[i]
        # Patrón de 3 filas: Team / Player / datos
        if pd.notna(row['Team']) and pd.isna(row['Player']) and i+2 < len(df):
            team = str(row['Team']).strip()
            player_row = df.iloc[i+1]
            data_row = df.iloc[i+2]
            if team == equipo:
                rows.append({
                    'Team':   team,
                    'Player': str(player_row['Player']).strip().title(),
                    'Event':  str(data_row['Player']).strip().lower(),
                    'Mins':   data_row['Event'],
                    'Secs':   data_row['Mins'],
                    'X':      data_row['Secs'],
                    'Y':      data_row['X'],
                    'X2':     data_row['Y'],
                    'Y2':     data_row['X2'],
                    'mitad':  mitad,
                    'fecha':  fecha,
                })
            i += 3
        else:
            i += 1

    clean = pd.DataFrame(rows)
    if clean.empty:
        return clean

    clean[['Mins','Secs','X','Y']] = clean[['Mins','Secs','X','Y']].apply(pd.to_numeric, errors='coerce')
    clean['X2'] = pd.to_numeric(clean['X2'], errors='coerce')
    clean['Y2'] = pd.to_numeric(clean['Y2'], errors='coerce')

    # Normalizar dirección: si atacan de der→izq, espejamos para que siempre sea izq→der
    if espejo:
        clean['X']  = 100 - clean['X']
        clean['Y']  = 100 - clean['Y']
        clean['X2'] = 100 - clean['X2']
        clean['Y2'] = 100 - clean['Y2']

    # Ajustar minutos del segundo tiempo
    if mitad == 2:
        clean['Mins'] = clean['Mins'] + 45

    clean['tiempo_total'] = clean['Mins'] * 60 + clean['Secs']

    return clean

def main():
    parser = argparse.ArgumentParser(description='Procesar partido y agregar a events_clean.csv')
    parser.add_argument('--pt',     required=True,  help='CSV primer tiempo')
    parser.add_argument('--st',     required=True,  help='CSV segundo tiempo')
    parser.add_argument('--fecha',  required=True,  type=int, help='Número de fecha')
    parser.add_argument('--dir_pt', default='izq',  choices=['izq','der'], help='Dirección ataque PT')
    parser.add_argument('--dir_st', default='der',  choices=['izq','der'], help='Dirección ataque ST')
    parser.add_argument('--output', default='data/events_clean.csv', help='Ruta al events_clean.csv')
    parser.add_argument('--equipo', default='Estrella', help='Nombre del equipo en el CSV')
    args = parser.parse_args()

    print(f"\n📂 Procesando Fecha {args.fecha}...")
    print(f"   Primer tiempo:  {args.pt} (ataque {args.dir_pt}→{'der' if args.dir_pt=='izq' else 'izq'})")
    print(f"   Segundo tiempo: {args.st} (ataque {args.dir_st}→{'der' if args.dir_st=='izq' else 'izq'})")

    espejo_pt = args.dir_pt == 'der'
    espejo_st = args.dir_st == 'der'

    pt = parsear_mitad(args.pt, mitad=1, fecha=args.fecha, espejo=espejo_pt, equipo=args.equipo)
    st = parsear_mitad(args.st, mitad=2, fecha=args.fecha, espejo=espejo_st, equipo=args.equipo)

    nuevo = pd.concat([pt, st], ignore_index=True)
    print(f"\n✅ Eventos procesados: {len(pt)} (PT) + {len(st)} (ST) = {len(nuevo)} total")
    print(f"   Tipos de eventos: {nuevo['Event'].value_counts().to_dict()}")

    # Cargar histórico y verificar que no exista ya esta fecha
    if os.path.exists(args.output):
        historico = pd.read_csv(args.output)
        if args.fecha in historico['fecha'].values:
            print(f"\n⚠️  La Fecha {args.fecha} ya existe en {args.output}.")
            resp = input("   ¿Sobreescribir? (s/n): ").strip().lower()
            if resp != 's':
                print("   Cancelado.")
                return
            historico = historico[historico['fecha'] != args.fecha]
        final = pd.concat([historico, nuevo], ignore_index=True)
    else:
        final = nuevo

    final.to_csv(args.output, index=False)
    print(f"\n💾 Guardado en {args.output}")
    print(f"   Total eventos históricos: {len(final)}")
    print(f"   Fechas en el archivo: {sorted(final['fecha'].unique().tolist())}\n")

if __name__ == '__main__':
    main()