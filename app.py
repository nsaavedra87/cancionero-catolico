import streamlit as st
import pandas as pd
import os
import re

# --- CONFIGURACIÓN DE ARCHIVOS ---
DB_FILE = "cancionero.csv"
CAT_DEFAULT = ["Entrada", "Piedad", "Gloria", "Aleluya", "Ofertorio", "Santo", "Cordero", "Comunión", "Salida", "María", "Adoración"]

def cargar_datos():
    try:
        if os.path.exists(DB_FILE) and os.path.getsize(DB_FILE) > 0:
            return pd.read_csv(DB_FILE)
    except Exception: pass
    return pd.DataFrame(columns=["Título", "Categoría", "Letra"])

def guardar_datos(df):
    df.to_csv(DB_FILE, index=False)

# --- MOTOR DE RENDERIZADO (Mantiene alineación y quita barra blanca) ---
def procesar_texto_estricto(texto, color_acorde):
    if not texto: return ""
    # Detecta acordes en notación americana (A, B, C) y latina (Do, Re, Mi)
    patron = r"\b([A-G][#b]?(m|maj|7|9|sus\d|dim|aug|add\d)?)\b|\b(Do|Re|Mi|Fa|Sol|La|Si)[#b]?(m|maj|7|9|sus\d|dim|aug|add\d)?\b"
    
    def reemplazar(match):
        acorde = match.group(0)
        return f'<span style="color:{color_acorde}; font-weight:bold;">{acorde}</span>'
    
    lineas = texto.split('\n')
    lineas_procesadas = []
    for linea in lineas:
        # SOLUCIÓN BARRA BLANCA: Si la línea está vacía, ponemos un espacio invisible
        if not linea.strip():
            lineas_procesadas.append("&nbsp;")
            continue
        
        # Colorear acordes y convertir espacios en puntos fijos para que no se muevan
        linea_color = re.sub(patron, reemplazar, linea)
        linea_final = linea_color.replace(" ", "&nbsp;")
        lineas_procesadas.append(linea_final)
        
    return "<br>".join(lineas_procesadas)

# --- INTERFAZ ---
st.set_page_config(page_title="ChordMaster Lite", page_icon="🎸", layout="wide")

# CSS para forzar fuente monoespaciada (vital para alineación)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&display=swap');
    textarea { 
        font-family: 'JetBrains Mono', monospace !important; 
        font-size: 16px !important; 
        background-color: #000 !important; 
        color: #ddd !important; 
    }
    .visor-musical { 
        border-radius: 8px; 
        padding: 20px; 
        background-color: #121212; 
        border: 1px solid #333; 
        font-family: 'JetBrains Mono', monospace !important; 
        line-height: 1.2; 
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

df = cargar_datos()

# --- SIDEBAR ---
st.sidebar.title("🎸 ChordMaster")
menu = st.sidebar.selectbox("Ir a:", ["🏠 Cantar / Buscar", "➕ Agregar Canción", "📂 Gestionar Biblioteca"])
c_chord = st.sidebar.color_picker("Color Acordes", "#FFD700")
f_size = st.sidebar.slider("Tamaño Fuente", 12, 45, 20)

# --- MÓDULO: AGREGAR ---
if menu == "➕ Agregar Canción":
    st.header("➕ Agregar Nueva Canción")
    col1, col2 = st.columns(2)
    with col1: titulo_n = st.text_input("Título")
    with col2: cat_n = st.selectbox("Momento Litúrgico", CAT_DEFAULT)
    
    letra_n = st.text_area("Editor (Alinea los acordes sobre las letras con espacios):", height=400)
    
    if letra_n:
        st.subheader("👀 Vista Previa (Lo que ves es lo que queda)")
        preview = procesar_texto_estricto(letra_n, c_chord)
        st.markdown(f'<div class="visor-musical" style="font-size:{f_size}px;">{preview}</div>', unsafe_allow_html=True)
        
        if st.button("💾 GUARDAR CANCIÓN", use_container_width=True):
            if titulo_n:
                nueva = pd.DataFrame([[titulo_n, cat_n, letra_n]], columns=df.columns)
                df = pd.concat([df, nueva], ignore_index=True)
                guardar_datos(df)
                st.success(f"¡{titulo_n} guardada!")
                st.rerun()

# --- MÓDULO: CANTAR ---
elif menu == "🏠 Cantar / Buscar":
    st.header("🏠 Biblioteca de Cantos")
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1: busqueda = st.text_input("🔍 Buscar por nombre...")
    with col_f2: filtro_cat = st.selectbox("📂 Momento Litúrgico", ["Todas"] + CAT_DEFAULT)

    df_v = df.copy()
    if busqueda: df_v = df_v[df_v['Título'].str.contains(busqueda, case=False)]
    if filtro_cat != "Todas": df_v = df_v[df_v['Categoría'] == filtro_cat]

    if not df_v.empty:
        seleccion = st.selectbox("Selecciona:", df_v['Título'])
        data_c = df_v[df_v['Título'] == seleccion].iloc[0]
        
        st.divider()
        st.subheader(f"{data_c['Título']} - {data_c['Categoría']}")
        final = procesar_texto_estricto(data_c['Letra'], c_chord)
        st.markdown(f'<div class="visor-musical" style="font-size:{f_size}px;">{final}</div>', unsafe_allow_html=True)

# --- MÓDULO: GESTIONAR ---
elif menu == "📂 Gestionar Biblioteca":
    st.header("📂 Gestión de Archivos")
    st.dataframe(df, use_container_width=True)
    if st.button("Eliminar última canción añadida"):
        df = df[:-1]
        guardar_datos(df)
        st.rerun()
