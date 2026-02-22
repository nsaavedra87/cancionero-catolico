import streamlit as st
import pandas as pd
import os
import re

# --- CONFIGURACIÓN ---
DB_FILE = "cancionero.csv"

def cargar_datos():
    if os.path.exists(DB_FILE) and os.path.getsize(DB_FILE) > 0:
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Título", "Autor", "Categoría", "Letra"])

def guardar_datos(df):
    df.to_csv(DB_FILE, index=False)

# --- INTERFAZ ULTRA-LIMPIA ---
st.set_page_config(page_title="ChordMaster Stage", layout="wide")

# CSS DE NIVEL PROFESIONAL PARA ALINEACIÓN
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    
    /* Forzar fuente monoespaciada en TODA la app */
    * { font-family: 'JetBrains Mono', monospace !important; }

    /* El Editor: un espejo de la realidad */
    .stTextArea textarea {
        background-color: #050505 !important;
        color: #e0e0e0 !important;
        font-size: 18px !important;
        line-height: 1.2 !important;
        border: 1px solid #333 !important;
    }

    /* El Visor de Escenario: Sin espacios extra, sin saltos raros */
    .visor-musical {
        background-color: #000000;
        padding: 30px;
        border-radius: 10px;
        border: 2px solid #1a1a1a;
        white-space: pre; /* Crucial: Respeta espacios exactos */
        overflow-x: auto;
        line-height: 1.1;
    }
    </style>
    """, unsafe_allow_html=True)

df = cargar_datos()

# --- SIDEBAR COMPACTO ---
menu = st.sidebar.radio("Modo:", ["🏠 En Vivo", "📝 Editor Maestro", "📂 Biblioteca"])
c_chord = st.sidebar.color_picker("Color Acordes", "#00FFCC")
f_size = st.sidebar.slider("Tamaño de Letra", 14, 45, 24)

if menu == "📝 Editor Maestro":
    st.header("📝 Editor de Cifrado Libre")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        t = st.text_input("Título de la Canción", placeholder="Ej: Pescador de Hombres")
        # El usuario escribe libremente aquí
        letra_raw = st.text_area("Escribe acordes arriba y letra abajo (usa espacios para alinear):", 
                                 height=500,
                                 placeholder="Do          Sol\nTú, has venido a la orilla...")
        
        if st.button("✨ Limpiar caracteres extraños"):
            # Solo deja letras, números, símbolos de acordes y espacios
            letra_raw = re.sub(r'[^a-zA-Z0-9#b7m\sáéíóúÁÉÍÓÚñÑ+]', '', letra_raw)
            st.rerun()

    with col2:
        st.write("### 🎹 Guía de Piano")
        # Diccionario visual rápido
        acorde_guia = st.selectbox("Ver notas de:", ["C", "Cm", "D", "Dm", "E", "Em", "F", "Fm", "G", "Gm", "A", "Am", "B", "Bm"])
        notas = {
            "C": "Do-Mi-Sol", "Cm": "Do-Mib-Sol", "D": "Re-Fa#-La", "Dm": "Re-Fa-La",
            "E": "Mi-Sol#-Si", "Em": "Mi-Sol-Si", "F": "Fa-La-Do", "Fm": "Fa-Lab-Do",
            "G": "Sol-Si-Re", "Gm": "Sol-Sib-Re", "A": "La-Do#-Mi", "Am": "La-Do-Mi",
            "B": "Si-Re#-Fa#", "Bm": "Si-Re-Fa#"
        }
        st.info(f"Notas: **{notas[acorde_guia]}**")
        
        # Imagen estática de referencia
        

    if letra_raw:
        st.divider()
        st.subheader("👀 Vista Previa de Escenario")
        # Procesamos el color de los acordes en tiempo real
        patron = r"\b([A-G][#b]?(m|maj|7|9|sus\d|dim|aug|add\d)?)\b"
        preview_coloreada = re.sub(patron, f'<span style="color:{c_chord}; font-weight:bold;">\\1</span>', letra_raw)
        
        st.markdown(f"""
            <div class="visor-musical" style="font-size:{f_size}px;">{preview_coloreada}</div>
        """, unsafe_allow_html=True)
        
        if st.button("💾 GUARDAR CANCIÓN", use_container_width=True):
            nueva = pd.DataFrame([[t, "Autor", "General", letra_raw]], columns=df.columns)
            df = pd.concat([df, nueva], ignore_index=True)
            guardar_datos(df)
            st.success("¡Guardada!")

elif menu == "🏠 En Vivo":
    if not df.empty:
        sel = st.selectbox("Seleccionar:", df['Título'])
        cancion = df[df['Título'] == sel].iloc[0]
        
        patron = r"\b([A-G][#b]?(m|maj|7|9|sus\d|dim|aug|add\d)?)\b"
        texto_final = re.sub(patron, f'<span style="color:{c_chord}; font-weight:bold;">\\1</span>', cancion['Letra'])
        
        st.markdown(f"""
            <div class="visor-musical" style="font-size:{f_size}px;">
            <h1 style="color:white; margin-bottom:20px;">{cancion['Título']}</h1>
{texto_final}
            </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("No hay canciones en la biblioteca.")

elif menu == "📂 Biblioteca":
    st.header("📂 Biblioteca")
    st.dataframe(df[['Título', 'Autor', 'Categoría']], use_container_width=True)
    if st.button("Borrar última canción añadida"):
        df = df[:-1]
        guardar_datos(df)
        st.rerun()
