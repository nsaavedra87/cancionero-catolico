import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import pytesseract # Requiere configuración en el servidor
import streamlit.components.v1 as components

# --- CONFIGURACIÓN DE BASE DE DATOS ---
DB_FILE = "cancionero.csv"

def cargar_datos():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Título", "Autor", "Temática", "Letra"])

def guardar_datos(df):
    df.to_csv(DB_FILE, index=False)

# --- LÓGICA MUSICAL ---
NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def transponer_texto(texto, semitonos):
    if semitonos == 0 or not texto: return texto
    patron = r"\b([A-G][#b]?(m|maj|7|9|sus\d|dim|aug|add\d)?)\b"
    def reemplazar(match):
        acorde = match.group(1)
        match_nota = re.match(r"([A-G][#b]?)", acorde)
        nota_original = match_nota.group(1)
        dic_bemoles = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
        nota_base = dic_bemoles.get(nota_original, nota_original)
        resto = acorde[len(nota_original):]
        if nota_base in NOTAS:
            nueva_nota = NOTAS[(NOTAS.index(nota_base) + semitonos) % 12]
            return nueva_nota + resto
        return acorde
    return re.sub(patron, reemplazar, texto)

# --- INTERFAZ ---
st.set_page_config(page_title="ChordMaster Pro OCR", layout="wide")

# Sidebar: Personalización y Navegación
st.sidebar.title("🎨 Configuración")
color_bg = st.sidebar.color_picker("Fondo del Visor", "#1E1E1E")
color_txt = st.sidebar.color_picker("Color de Letra", "#00FF00")
f_size = st.sidebar.slider("Tamaño de letra", 14, 36, 22)

st.sidebar.divider()
menu = st.sidebar.radio("Ir a:", ["Cantar (Live)", "Añadir por Foto 📸", "Añadir Manual 📝", "Mi Setlist 📋"])

df = cargar_datos()

if menu == "Añadir por Foto 📸":
    st.header("📷 Importar desde Foto / Cámara")
    st.info("Toma una foto a tu letra escrita a mano. El sistema intentará extraer el texto.")
    
    img_file = st.camera_input("Capturar letra")
    if img_file:
        img = Image.open(img_file)
        # Aquí se ejecuta el OCR
        with st.spinner("Leyendo manuscrito..."):
            try:
                texto_extraido = pytesseract.image_to_string(img, lang='spa')
                st.subheader("Texto detectado:")
                letra_edit = st.text_area("Edita la letra y añade los acordes:", texto_extraido, height=300)
                
                col1, col2 = st.columns(2)
                tit = col1.text_input("Título")
                aut = col2.text_input("Autor")
                
                if st.button("Guardar en Cancionero"):
                    nueva = pd.DataFrame([[tit, aut, "Foto", letra_edit]], columns=df.columns)
                    df = pd.concat([df, nueva], ignore_index=True)
                    guardar_datos(df)
                    st.success("¡Canción guardada con éxito!")
            except:
                st.error("Error al leer la imagen. Asegúrate de tener buena luz.")

elif menu == "Añadir Manual 📝":
    st.header("📝 Registro Manual")
    with st.form("form_manual"):
        t = st.text_input("Título")
        a = st.text_input("Autor")
        tem = st.selectbox("Temática", ["Rock", "Pop", "Alabanza", "Otro"])
        let = st.text_area("Letra y Acordes", height=300)
        if st.form_submit_button("Guardar"):
            nueva = pd.DataFrame([[t, a, tem, let]], columns=df.columns)
            df = pd.concat([df, nueva], ignore_index=True)
            guardar_datos(df)
            st.success("¡Guardada!")

elif menu == "Cantar (Live)":
    st.header("🎤 Modo Presentación")
    if not df.empty:
        c_sel = st.selectbox("Selecciona Canción", df['Título'])
        datos = df[df['Título'] == c_sel].iloc[0]
        
        col1, col2, col3 = st.columns(3)
        tono = col1.slider("Transponer", -6, 6, 0)
        vel = col2.slider("Auto-Scroll", 0, 10, 0)
        if col3.button("⭐ Subir al Setlist"):
            if 'setlist' not in st.session_state: st.session_state.setlist = []
            st.session_state.setlist.append(c_sel)
            st.toast("Añadida")

        if vel > 0:
            components.html(f"<script>setInterval(()=>window.scrollBy(0,1),{100/vel});</script>", height=0)

        # Visor con Estilos
        letra_f = transponer_texto(datos['Letra'], tono)
        st.markdown(f"""
            <div style="background:{color_bg}; color:{color_txt}; font-size:{f_size}px; 
            font-family:monospace; padding:30px; border-radius:15px; white-space:pre-wrap;">
            {letra_f}
            </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("No hay canciones. ¡Agrega una!")

elif menu == "Mi Setlist 📋":
    st.header("📋 Setlist del Día")
    if 'setlist' in st.session_state and st.session_state.setlist:
        for s in st.session_state.setlist:
            st.write(f"🎵 {s}")
        if st.button("Limpiar todo"):
            st.session_state.setlist = []
            st.rerun()
    else:
        st.info("Lista vacía.")
