import streamlit as st
import pandas as pd
import os
import re

# --- CONFIGURACIÓN DE ARCHIVOS ---
DB_FILE = "cancionero.csv"
CAT_FILE = "categorias.csv"
SETLIST_FILE = "setlist_fijo.csv"

# --- FUNCIONES DE DATOS ---
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

# --- LÓGICA DE TRANSPOSICIÓN LIMPIA ---
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
        
        # Identificar si es línea de acordes (alta densidad de espacios o palabras cortas)
        es_linea_acordes = (linea.count(" ") / len(linea)) > 0.15 if len(linea) > 6 else True
        
        # Procesar transposición
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

        # Envolver en clase de acorde si corresponde (CSS aplicará la negrita)
        if es_linea_acordes:
            lineas_finales.append(f'<span class="chord-line">{linea}</span>')
        else:
            lineas_finales.append(linea)
            
    return "\n".join(lineas_finales)

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ChordMaster Pro", layout="wide")
if 'setlist' not in st.session_state: st.session_state.setlist = cargar_setlist()

# Sidebar y Estilos
st.sidebar.title("🎸 ChordMaster")
menu = st.sidebar.selectbox("Ir a:", ["🏠 Vivo", "📋 Setlist", "➕ Agregar", "📂 Editar", "⚙️ Categorías"])
st.sidebar.markdown("---")
c_bg = st.sidebar.color_picker("Fondo Visor", "#FFFFFF")
c_txt = st.sidebar.color_picker("Color Letra", "#000000")
f_size = st.sidebar.slider("Tamaño Fuente", 12, 45, 19)

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&display=swap');
    .visor-musical {{ 
        background-color: {c_bg} !important; 
        color: {c_txt} !important; 
        border-radius: 12px; padding: 25px; border: 1px solid #ddd; 
        font-family: 'JetBrains Mono', monospace !important; 
        line-height: 1.5; font-size: {f_size}px;
        white-space: pre !important; 
    }}
    .chord-line {{ font-weight: 800 !important; color: inherit; }}
    </style>
    """, unsafe_allow_html=True)

df = cargar_datos()
categorias = cargar_categorias()

# --- MODULO VIVO ---
if menu == "🏠 Vivo":
    busqueda = st.text_input("🔍 Buscar canción...")
    df_v = df[df['Título'].str.contains(busqueda, case=False, na=False)] if busqueda else df
    
    if not df_v.empty:
        sel_c = st.selectbox("Seleccionar:", df_v['Título'])
        data = df_v[df_v['Título'] == sel_c].iloc[0]
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("➕ Añadir al Setlist"):
                if sel_c not in st.session_state.setlist:
                    st.session_state.setlist.append(sel_c)
                    guardar_setlist(st.session_state.setlist)
                    st.toast("¡Añadida!")
        with col2:
            tp = st.number_input("Transportar (Semitonos)", -6, 6, 0)

        cuerpo = procesar_texto_final(data['Letra'], tp)
        st.markdown(f'''<div class="visor-musical"><b>{data["Título"]}</b>
{data["Autor"]} | <i>{data["Categoría"]}</i>
<hr style="border: 0.5px solid {c_txt}; opacity: 0.2;">
{cuerpo}</div>''', unsafe_allow_html=True)

# --- MODULO SETLIST ---
elif menu == "📋 Setlist":
    st.header("📋 Mi Setlist")
    if not st.session_state.setlist:
        st.info("No hay canciones seleccionadas.")
    else:
        for i, t in enumerate(st.session_state.setlist):
            col_exp, col_del = st.columns([6, 1])
            with col_exp:
                with st.expander(f"🎵 {t}"):
                    cancion_row = df[df['Título'] == t]
                    if not cancion_row.empty:
                        data = cancion_row.iloc[0]
                        tp_sl = st.number_input("Tono", -6, 6, 0, key=f"tp_sl_{i}")
                        st.markdown(f'<div class="visor-musical">{procesar_texto_final(data["Letra"], tp_sl)}</div>', unsafe_allow_html=True)
            with col_del:
                if st.button("🗑️", key=f"del_{i}", help="Eliminar del setlist"):
                    st.session_state.setlist.pop(i)
                    guardar_setlist(st.session_state.setlist)
                    st.rerun()

# --- MODULO AGREGAR ---
elif menu == "➕ Agregar":
    st.header("➕ Nueva Canción")
    c1, c2, c3 = st.columns(3)
    t_n = c1.text_input("Título")
    a_n = c2.text_input("Autor")
    cat_n = c3.selectbox("Categoría", categorias)
    l_n = st.text_area("Letra y Acordes:", height=300)
    
    if l_n:
        st.subheader("👀 Vista Previa")
        st.markdown(f'<div class="visor-musical">{procesar_texto_final(l_n, 0)}</div>', unsafe_allow_html=True)
        
    if st.button("💾 Guardar Canción"):
        if t_n and l_n:
            nueva = pd.DataFrame([[t_n, a_n if a_n else "Anónimo", cat_n, l_n]], columns=df.columns)
            df = pd.concat([df, nueva], ignore_index=True)
            guardar_datos(df)
            st.success("¡Guardada!")
            st.rerun()

# --- MODULO EDITAR ---
elif menu == "📂 Editar":
    st.header("📂 Gestionar Biblioteca")
    for i, row in df.iterrows():
        with st.expander(f"📝 {row['Título']}"):
            ut = st.text_input("Título", row['Título'], key=f"ut{i}")
            ua = st.text_input("Autor", row['Autor'], key=f"ua{i}")
            uc = st.selectbox("Categoría", categorias, index=categorias.index(row['Categoría']) if row['Categoría'] in categorias else 0, key=f"uc{i}")
            ul = st.text_area("Letra", row['Letra'], height=200, key=f"ul{i}")
            c_ed1, c_ed2 = st.columns(2)
            if c_ed1.button("Actualizar", key=f"ub{i}"):
                df.at[i, 'Título'], df.at[i, 'Autor'], df.at[i, 'Categoría'], df.at[i, 'Letra'] = ut, ua, uc, ul
                guardar_datos(df); st.rerun()
            if c_ed2.button("Eliminar permanentemente", key=f"ud{i}"):
                df = df.drop(i).reset_index(drop=True)
                guardar_datos(df); st.rerun()

# --- MODULO CATEGORÍAS ---
elif menu == "⚙️ Categorías":
    st.header("⚙️ Configuración de Categorías")
    for c in categorias:
        c1, c2 = st.columns([4, 1])
        c1.write(f"• {c}")
        if c2.button("Eliminar", key=f"cat_del_{c}"):
            categorias.remove(c)
            guardar_categorias(categorias); st.rerun()
    st.markdown("---")
    n_cat = st.text_input("Nueva categoría:")
    if st.button("Añadir"):
        if n_cat and n_cat not in categorias:
            categorias.append(n_cat)
            guardar_categorias(categorias); st.rerun()
