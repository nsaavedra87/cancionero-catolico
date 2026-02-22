import streamlit as st
import pandas as pd
import os
import re

# --- CONFIGURACIÓN DE ARCHIVOS ---
DB_FILE = "cancionero.csv"
CAT_FILE = "categorias.csv"
SETLIST_FILE = "setlist_fijo.csv"

# --- FUNCIONES DE DATOS (MANTENIDAS) ---
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

# --- LÓGICA DE PROCESAMIENTO MUSICAL MEJORADA ---
NOTAS_LAT = ["Do", "Do#", "Re", "Re#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"]
NOTAS_AMER = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def transportar_nota(nota, semitonos):
    for lista in [NOTAS_AMER, NOTAS_LAT]:
        if nota in lista:
            idx = (lista.index(nota) + semitonos) % 12
            return lista[idx]
    return nota

def procesar_palabra_estricta(palabra, semitonos, es_linea_acordes):
    patron = r"^(Do#?|Re#?|Mi|Fa#?|Sol#?|La#?|Si|[A-G][#b]?)([\#bmM79dimatusj0-9]*)$"
    match = re.match(patron, palabra)
    if match:
        raiz, resto = match.group(1), match.group(2)
        if raiz in ["Si", "La", "A"] and not resto and not es_linea_acordes:
            return palabra
        
        # Transposición
        nueva_nota = palabra
        if semitonos != 0:
            dic_bemoles = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
            nota_busqueda = dic_bemoles.get(raiz, raiz)
            nueva_raiz = transportar_nota(nota_busqueda, semitonos)
            nueva_nota = f"{nueva_raiz}{resto}"
            
        return f"<b>{nueva_nota}</b>" # Devolvemos HTML limpio
    return palabra

def procesar_texto_final(texto, semitonos):
    if not texto: return ""
    lineas_finales = []
    for linea in texto.split('\n'):
        if not linea.strip(): 
            lineas_finales.append("")
            continue
        # Detección de línea de acordes
        es_linea_acordes = (linea.count(" ") / len(linea)) > 0.15 if len(linea) > 6 else True
        
        # Procesar palabra por palabra manteniendo espacios exactos
        palabras = re.split(r"(\s+)", linea)
        nueva_linea = "".join([p if p.strip() == "" else procesar_palabra_estricta(p, semitonos, es_linea_acordes) for p in palabras])
        lineas_finales.append(nueva_linea)
    return "\n".join(lineas_finales)

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="ChordMaster Pro", layout="wide")
if 'setlist' not in st.session_state: st.session_state.setlist = cargar_setlist()

# CSS Definitivo para corregir f63084
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&display=swap');
    .visor-musical {{ 
        background-color: white !important; 
        color: black !important; 
        border-radius: 8px; padding: 20px; border: 1px solid #eee; 
        font-family: 'JetBrains Mono', monospace !important; 
        font-size: 18px;
        white-space: pre !important; 
        line-height: 1.5;
        overflow-x: auto;
    }}
    .visor-musical b {{ font-weight: bold !important; color: #000; }}
    </style>
    """, unsafe_allow_html=True)

df = cargar_datos()
categorias = cargar_categorias()

# --- NAVEGACIÓN ---
menu = st.sidebar.selectbox("Menú", ["🏠 Vivo", "📋 Setlist", "➕ Agregar", "📂 Editar", "⚙️ Categorías"])

if menu == "🏠 Vivo":
    busqueda = st.text_input("🔍 Buscar canción")
    df_v = df[df['Título'].str.contains(busqueda, case=False)] if busqueda else df
    if not df_v.empty:
        sel = st.selectbox("Seleccionar", df_v['Título'])
        data = df_v[df_v['Título'] == sel].iloc[0]
        tp = st.number_input("Transportar", -6, 6, 0)
        
        cuerpo = procesar_texto_final(data['Letra'], tp)
        st.markdown(f'<div class="visor-musical"><b>{data["Título"]}</b>\n{data["Autor"]} | {data["Categoría"]}\n\n{cuerpo}</div>', unsafe_allow_html=True)

elif menu == "📋 Mi Setlist":
    st.header("📋 Mi Setlist")
    for i, t in enumerate(st.session_state.setlist):
        with st.expander(f"🎵 {t}"):
            cancion = df[df['Título'] == t].iloc[0]
            tp_sl = st.number_input("Tono", -6, 6, 0, key=f"tp{i}")
            st.markdown(f'<div class="visor-musical">{procesar_texto_final(cancion["Letra"], tp_sl)}</div>', unsafe_allow_html=True)
            if st.button("Quitar", key=f"del{i}"):
                st.session_state.setlist.pop(i); guardar_setlist(st.session_state.setlist); st.rerun()

elif menu == "➕ Agregar":
    t = st.text_input("Título")
    a = st.text_input("Autor")
    c = st.selectbox("Categoría", categorias)
    l = st.text_area("Letra y Acordes", height=300)
    
    if l:
        st.subheader("👀 Vista Previa")
        # Aquí forzamos el renderizado HTML para que procese las etiquetas <b>
        st.markdown(f'<div class="visor-musical">{procesar_texto_final(l, 0)}</div>', unsafe_allow_html=True)
        
    if st.button("Guardar"):
        nuevo = pd.DataFrame([[t, a, c, l]], columns=df.columns)
        df = pd.concat([df, nuevo]); guardar_datos(df); st.success("Guardado")
