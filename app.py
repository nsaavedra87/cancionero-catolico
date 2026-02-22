import streamlit as st
import pandas as pd
import os
import re

# --- CONFIGURACIÓN DE ARCHIVOS (MANTENIDO) ---
DB_FILE = "cancionero.csv"
CAT_FILE = "categorias.csv"
SETLIST_FILE = "setlist_fijo.csv"

def cargar_datos():
    try:
        if os.path.exists(DB_FILE) and os.path.getsize(DB_FILE) > 0:
            return pd.read_csv(DB_FILE)
    except Exception: pass
    return pd.DataFrame(columns=["Título", "Autor", "Categoría", "Letra"])

def cargar_categorias():
    cat_emergencia = ["Entrada", "Piedad", "Gloria", "Aleluya", "Ofertorio", "Santo", "Cordero", "Comunión", "Salida", "Adoración", "María"]
    try:
        if os.path.exists(CAT_FILE) and os.path.getsize(CAT_FILE) > 0:
            df_cat = pd.read_csv(CAT_FILE)
            return df_cat.iloc[:, 0].dropna().unique().tolist()
    except Exception: pass
    return cat_emergencia

def cargar_setlist():
    try:
        if os.path.exists(SETLIST_FILE) and os.path.getsize(SETLIST_FILE) > 0:
            return pd.read_csv(SETLIST_FILE)["Título"].tolist()
    except Exception: pass
    return []

def guardar_datos(df): df.to_csv(DB_FILE, index=False)
def guardar_categorias(lista_cat): pd.DataFrame(lista_cat, columns=["Nombre"]).to_csv(CAT_FILE, index=False)
def guardar_setlist(lista_sl): pd.DataFrame(lista_sl, columns=["Título"]).to_csv(SETLIST_FILE, index=False)

# --- LÓGICA DE TRANSPOSICIÓN LIMPIA (SIN HTML) ---
NOTAS_LAT = ["Do", "Do#", "Re", "Re#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"]
NOTAS_AMER = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def transportar_nota(nota, semitonos):
    for lista in [NOTAS_AMER, NOTAS_LAT]:
        if nota in lista:
            idx = (lista.index(nota) + semitonos) % 12
            return lista[idx]
    return nota

def procesar_texto_final(texto, semitonos):
    if not texto: return ""
    lineas_finales = []
    for linea in texto.split('\n'):
        if not linea.strip(): 
            lineas_finales.append("")
            continue
        
        # Detectar si es una línea de acordes
        es_linea_acordes = (linea.count(" ") / len(linea)) > 0.15 if len(linea) > 6 else True
        
        # Procesar transposición si es necesario
        if semitonos != 0:
            palabras = re.split(r"(\s+)", linea)
            nueva_linea = ""
            for p in palabras:
                patron = r"^(Do#?|Re#?|Mi|Fa#?|Sol#?|La#?|Si|[A-G][#b]?)([\#bmM79dimatusj0-9]*)$"
                match = re.match(patron, p)
                if match:
                    raiz, resto = match.group(1), match.group(2)
                    dic_bemoles = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
                    nueva_raiz = transportar_nota(dic_bemoles.get(raiz, raiz), semitonos)
                    nueva_linea += f"{nueva_raiz}{resto}"
                else:
                    nueva_linea += p
            linea = nueva_linea

        # Envolver líneas de acordes para ponerlas en negrita vía CSS
        if es_linea_acordes:
            lineas_finales.append(f'<span class="acorde-row">{linea}</span>')
        else:
            lineas_finales.append(linea)
            
    return "\n".join(lineas_finales)

# --- INTERFAZ ---
st.set_page_config(page_title="ChordMaster Pro", layout="wide")
if 'setlist' not in st.session_state: st.session_state.setlist = cargar_setlist()

# CSS Corregido para evitar errores visuales
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&display=swap');
    .visor-musical {{ 
        background-color: white; color: black; 
        border-radius: 8px; padding: 20px; border: 1px solid #eee; 
        font-family: 'JetBrains Mono', monospace !important; 
        font-size: 18px; white-space: pre !important; 
        line-height: 1.4; overflow-x: auto;
    }}
    .acorde-row {{ font-weight: bold !important; color: #d32f2f; }}
    </style>
    """, unsafe_allow_html=True)

df = cargar_datos()
categorias = cargar_categorias()

menu = st.sidebar.selectbox("Ir a:", ["🏠 Vivo", "📋 Setlist", "➕ Agregar", "📂 Editar", "⚙️ Categorías"])

if menu == "🏠 Vivo":
    busqueda = st.text_input("🔍 Buscar...")
    df_v = df[df['Título'].str.contains(busqueda, case=False)] if busqueda else df
    if not df_v.empty:
        sel_c = st.selectbox("Canción:", df_v['Título'])
        data = df_v[df_v['Título'] == sel_c].iloc[0]
        if st.button("➕ Al Setlist"):
            if sel_c not in st.session_state.setlist:
                st.session_state.setlist.append(sel_c)
                guardar_setlist(st.session_state.setlist); st.toast("Añadida")
        tp = st.number_input("Transportar", -6, 6, 0)
        cuerpo = procesar_texto_final(data['Letra'], tp)
        st.markdown(f'<div class="visor-musical"><b>{data["Título"]}</b>\n{data["Autor"]}\n\n{cuerpo}</div>', unsafe_allow_html=True)

elif menu == "📋 Setlist":
    st.header("📋 Mi Setlist")
    if not st.session_state.setlist: st.info("Setlist vacío")
    for i, t in enumerate(st.session_state.setlist):
        col_t, col_btn = st.columns([5, 1])
        with col_t:
            with st.expander(f"🎵 {t}"):
                cancion = df[df['Título'] == t].iloc[0]
                tp_sl = st.number_input("Tono", -6, 6, 0, key=f"tp{i}")
                st.markdown(f'<div class="visor-musical">{procesar_texto_final(cancion["Letra"], tp_sl)}</div>', unsafe_allow_html=True)
        with col_btn:
            if st.button("🗑️", key=f"del{i}", help="Eliminar del setlist"):
                st.session_state.setlist.pop(i); guardar_setlist(st.session_state.setlist); st.rerun()

elif menu == "➕ Agregar":
    st.header("➕ Nueva Canción")
    c1, c2, c3 = st.columns(3)
    t_n, a_n, cat_n = c1.text_input("Título"), c2.text_input("Autor"), c3.selectbox("Categoría", categorias)
    l_n = st.text_area("Letra y Acordes:", height=300)
    if l_n:
        st.subheader("👀 Vista Previa")
        st.markdown(f'<div class="visor-musical">{procesar_texto_final(l_n, 0)}</div>', unsafe_allow_html=True)
    if st.button("💾 Guardar"):
        nuevo = pd.DataFrame([[t_n, a_n, cat_n, l_n]], columns=df.columns)
        df = pd.concat([df, nuevo]); guardar_datos(df); st.success("¡Guardada!"); st.rerun()

# ... (El resto de módulos Editar y Categorías se mantienen igual)
