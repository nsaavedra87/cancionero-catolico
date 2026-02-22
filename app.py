import streamlit as st
import pandas as pd
import os
import re
from PIL import Image

# --- CONFIGURACIÓN DE ARCHIVOS ---
DB_FILE = "cancionero.csv"
CAT_FILE = "categorias.csv"

# --- FUNCIONES DE DATOS ---
def cargar_datos():
    try:
        if os.path.exists(DB_FILE) and os.path.getsize(DB_FILE) > 0:
            return pd.read_csv(DB_FILE)
    except Exception: pass
    return pd.DataFrame(columns=["Título", "Autor", "Categoría", "Letra"])

def cargar_categorias():
    cat_emergencia = ["Alabanza", "Adoracion", "Oracion", "Espiritu Santo", "Entrega", "Sanacion", "Amor de Dios", "Perdon", "Eucaristia-Entrada", "Eucaristia-Perdon", "Eucaristia-Gloria", "Eucaristia-Aclamacion", "Eucaristia Ofertorio", "Eucaristia-Santo", "Eucaristia-Cordero", "Eucaristia-Comunion", "Ecuaristia-Final", "Eucaristia-Maria", "Adviento", "Navidad", "Cuaresma"]
    try:
        if os.path.exists(CAT_FILE) and os.path.getsize(CAT_FILE) > 5:
            df_cat = pd.read_csv(CAT_FILE)
            return df_cat.iloc[:, 0].dropna().unique().tolist()
    except Exception: pass
    return cat_emergencia

def guardar_datos(df):
    df.to_csv(DB_FILE, index=False)

# --- LÓGICA DE PROCESAMIENTO VISUAL ---
NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def procesar_texto(texto, semitonos, color_acorde):
    if not texto: return ""
    # Patrón para detectar acordes (C, Dm, G7, etc.)
    patron = r"\b([A-G][#b]?(m|maj|7|9|sus\d|dim|aug|add\d)?)\b"
    
    def reemplazar(match):
        acorde = match.group(1)
        match_nota = re.match(r"([A-G][#b]?)", acorde)
        nota_original = match_nota.group(1)
        dic_bemoles = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
        nota_base = dic_bemoles.get(nota_original, nota_original)
        
        if nota_base in NOTAS and semitonos != 0:
            nueva_nota = NOTAS[(NOTAS.index(nota_base) + semitonos) % 12]
            acorde = nueva_nota + acorde[len(nota_original):]
        
        return f'<span style="color:{color_acorde}; font-weight:bold;">{acorde}</span>'
    
    return re.sub(patron, reemplazar, texto)

def limpiar_texto(t):
    # Elimina caracteres extraños, deja solo letras, números, acordes y puntuación básica
    t = re.sub(r'[^\w\s#+m7áéíóúÁÉÍÓÚñÑ.,\-()|/]', '', t)
    # Reduce espacios múltiples a uno solo
    t = re.sub(r' +', ' ', t)
    return t.strip()

# --- INTERFAZ ---
st.set_page_config(page_title="ChordMaster Pro", page_icon="🎸", layout="wide")

# CSS para Editor y Visor
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&family=Montserrat:wght@700&display=swap');
    [data-testid="stHeader"] {{ visibility: hidden; }}
    
    /* Forzar al editor de texto a usar fuente monoespaciada para que coincida con el visor */
    textarea {{
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 16px !important;
    }}
    
    .visor-musical {{
        border-radius: 12px;
        padding: 15px 25px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.3);
        border: 1px solid #444;
        white-space: pre; /* Mantiene espacios exactos */
        line-height: 1.2;
        overflow-x: auto;
    }}
    .titulo-visor {{ font-family: 'Montserrat', sans-serif; margin-bottom: 0px; line-height: 1.0; font-size: 1.5em; }}
    .autor-visor {{ color: #777; margin-bottom: 5px; font-size: 0.85em; }}
    </style>
    """, unsafe_allow_html=True)

df = cargar_datos()
categorias = cargar_categorias()

# --- SIDEBAR ---
st.sidebar.title("🎸 Menú")
menu = st.sidebar.selectbox("Ir a:", ["🏠 Cantar / Vivo", "➕ Agregar Canción", "📂 Gestionar Biblioteca", "⚙️ Categorías", "📋 Setlist"])

st.sidebar.divider()
st.sidebar.subheader("🎨 Ajustes de Vista")
c_bg = st.sidebar.color_picker("Fondo", "#121212")
c_txt = st.sidebar.color_picker("Letras", "#FFFFFF")
c_chord = st.sidebar.color_picker("Acordes", "#FFD700")
f_size = st.sidebar.slider("Tamaño Letra", 12, 40, 20)
f_family = "'JetBrains Mono', monospace" # Forzado para alineación

# --- MÓDULO: AGREGAR CANCIÓN ---
if menu == "➕ Agregar Canción":
    st.header("➕ Nueva Canción")
    
    metodo = st.radio("Origen:", ["Manual / Copiar Texto", "Escanear Foto (OCR)"], horizontal=True)
    
    if 'texto_temp' not in st.session_state: st.session_state.texto_temp = ""

    if metodo == "Escanear Foto (OCR)":
        img_file = st.camera_input("Capturar")
        if img_file:
            import pytesseract
            img = Image.open(img_file)
            with st.spinner("Leyendo..."):
                st.session_state.texto_temp = pytesseract.image_to_string(img, lang='spa')

    st.divider()
    
    col_input1, col_input2 = st.columns(2)
    titulo_n = col_input1.text_input("Título")
    autor_n = col_input2.text_input("Autor")
    cat_n = st.selectbox("Categoría", categorias)
    
    # Editor Monoespaciado
    letra_n = st.text_area("Editor (Usa espacios para alinear acordes sobre las letras):", 
                           value=st.session_state.texto_temp, 
                           height=350)
    
    col_btn1, col_btn2 = st.columns(2)
    if col_btn1.button("✨ Limpiar Texto (Quitar basura)"):
        st.session_state.texto_temp = limpiar_texto(letra_n)
        st.rerun()

    # Vista Previa Dinámica
    if letra_n:
        st.subheader("👀 Vista Previa (Alineación Real)")
        preview_html = procesar_texto(letra_n, 0, c_chord)
        st.markdown(f"""
            <div class="visor-musical" style="background:{c_bg}; color:{c_txt}; font-size:{f_size}px; font-family:{f_family};">
                <div class="titulo-visor" style="color:white;">{titulo_n if titulo_n else 'Título'}</div>
                <div class="autor-visor">{autor_n if autor_n else 'Autor'} | {cat_n}</div>
                <hr style="margin: 5px 0; border-color: #333;">
                {preview_html}
            </div>
        """, unsafe_allow_html=True)

        if st.button("💾 GUARDAR EN BIBLIOTECA", use_container_width=True):
            if titulo_n and letra_n:
                nueva_fila = pd.DataFrame([[titulo_n, autor_n, cat_n, letra_n]], columns=df.columns)
                df = pd.concat([df, nueva_fila], ignore_index=True)
                guardar_datos(df)
                st.success("¡Canción guardada!")
                st.session_state.texto_temp = ""
            else: st.error("Falta título o letra.")

# --- MÓDULO: CANTAR ---
elif menu == "🏠 Cantar / Vivo":
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1: b = st.text_input("🔍 Buscar...")
    with col_f2: f_cat = st.multiselect("🏷️ Categoría", categorias)

    df_v = df.copy()
    if b: df_v = df_v[df_v['Título'].str.contains(b, case=False, na=False) | df_v['Autor'].str.contains(b, case=False, na=False)]
    if f_cat: df_v = df_v[df_v['Categoría'].isin(f_cat)]

    if not df_v.empty:
        sel_c = st.selectbox("Selecciona:", df_v['Título'])
        data_c = df_v[df_v['Título'] == sel_c].iloc[0]
        
        col_c1, col_c2, col_c3 = st.columns(3)
        tp = col_c1.number_input("Transportar", -6, 6, 0)
        sc = col_c2.slider("Auto-Scroll", 0, 10, 0)
        if col_c3.button("⭐ Setlist"):
            st.session_state.setlist.append(sel_c); st.toast("Añadida")

        if sc > 0:
            st.components.v1.html(f"<script>setInterval(()=>window.parent.scrollBy(0,1),{100/sc});</script>", height=0)

        l_html = procesar_texto(data_c['Letra'], tp, c_chord)
        st.markdown(f"""
            <div class="visor-musical" style="background:{c_bg}; color:{c_txt}; font-size:{f_size}px; font-family:{f_family};">
                <div class="titulo-visor" style="color:white;">{data_c['Título']}</div>
                <div class="autor-visor">{data_c['Autor']} | {data_c['Categoría']}</div>
                {l_html}
            </div>
        """, unsafe_allow_html=True)

# --- GESTIONAR ---
elif menu == "📂 Gestionar Biblioteca":
    st.header("📂 Gestionar")
    for i, row in df.iterrows():
        with st.expander(f"{row['Título']}"):
            if st.button(f"Eliminar definitivamente", key=f"del_{i}"):
                df = df.drop(i).reset_index(drop=True)
                guardar_datos(df)
                st.rerun()

# --- CATEGORÍAS ---
elif menu == "⚙️ Categorías":
    st.header("⚙️ Categorías")
    n_cat = st.text_input("Nueva:")
    if st.button("Añadir"):
        if n_cat and n_cat not in categorias:
            categorias.append(n_cat)
            pd.DataFrame(categorias, columns=['Nombre']).to_csv(CAT_FILE, index=False)
            st.rerun()
    st.write(categorias)

elif menu == "📋 Setlist":
    st.header("📋 Setlist")
    for s in st.session_state.setlist: st.write(f"• {s}")
    if st.button("Limpiar"): st.session_state.setlist = []; st.rerun()
