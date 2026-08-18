import streamlit as st
import pandas as pd
import requests
import urllib.parse

# ID da Planilha e GIDs
DOC_ID = "1Dq9BXjt9tbsdFQryC3NBYJTXvhHjZbtEGdG_ZXpWdp0"

GIDS = {
    "LIVROS": "1591861167",
    "SÉRIES": "1513581778",
    "UNIVERSO MARVEL": "1360927897"
}

OMDB_API_KEY = "trilogy"

st.set_page_config(
    page_title="Procrastinação Organizada",
    page_icon="🍿",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #14181c; color: #9ab; }
    h1, h2, h3, h4 { color: #ffffff !important; }
    .stProgress > div > div > div > div { background-color: #00e054; }
    div[data-testid="stImage"] img {
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5) !important;
        object-fit: cover !important;
        aspect-ratio: 2/3 !important;
        width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

def generate_card_url(title, bg_color="1e293b", text_color="ffffff"):
    clean_title = str(title).strip()[:25] if pd.notna(title) else "Entretenimento"
    encoded_text = urllib.parse.quote(clean_title)
    return f"https://dummyimage.com/400x600/{bg_color}/{text_color}.png&text={encoded_text}"

# --- BUSCA DE LIVROS (MULTIFONTES: GOOGLE BOOKS + OPEN LIBRARY) ---
@st.cache_data(ttl=86400)
def get_book_cover(title, author=""):
    title_str = str(title).strip() if pd.notna(title) else ""
    if not title_str or title_str.lower() in ["nan", "none"]:
        return generate_card_url("Livro")
    
    query = f"{title_str} {author}".strip()
    encoded = urllib.parse.quote(query)

    # 1. Busca via Google Books (sem headers para não bloquear)
    try:
        url_gb = f"https://www.googleapis.com/books/v1/volumes?q={encoded}&maxResults=1"
        res_gb = requests.get(url_gb, timeout=3).json()
        if "items" in res_gb and len(res_gb["items"]) > 0:
            links = res_gb["items"][0].get("volumeInfo", {}).get("imageLinks", {})
            cover = links.get("thumbnail") or links.get("smallThumbnail")
            if cover:
                return cover.replace("http://", "https://")
    except Exception:
        pass

    # 2. Open Library (Backup)
    try:
        url_ol = f"https://openlibrary.org/search.json?q={encoded}"
        res_ol = requests.get(url_ol, timeout=3).json()
        if "docs" in res_ol and len(res_ol["docs"]) > 0:
            cover_i = res_ol["docs"][0].get("cover_i")
            if cover_i:
                return f"https://covers.openlibrary.org/b/id/{cover_i}-L.jpg"
    except Exception:
        pass
        
    return generate_card_url(title_str, bg_color="0f172a")

# --- BUSCA DE FILMES E SÉRIES COM MULTIBUSCA ---
@st.cache_data(ttl=86400)
def get_omdb_poster(title, media_type="movie"):
    title_str = str(title).strip() if pd.notna(title) else ""
    if not title_str or title_str.lower() in ["nan", "none"]:
        return generate_card_url("Mídia")
    
    encoded = urllib.parse.quote(title_str)
    type_clean = str(media_type).lower().strip()
    type_param = "series" if any(x in type_clean for x in ["série", "serie", "tv"]) else "movie"

    # 1. Busca Direta no OMDb com o título original em PT
    try:
        url = f"http://www.omdbapi.com/?t={encoded}&type={type_param}&apikey={OMDB_API_KEY}"
        res = requests.get(url, timeout=3).json()
        if res.get("Response") == "True" and res.get("Poster") and res["Poster"] != "N/A":
            return res["Poster"]
    except Exception:
        pass

    # 2. Busca Geral no OMDb por palavra-chave (Search s=)
    try:
        url_s = f"http://www.omdbapi.com/?s={encoded}&apikey={OMDB_API_KEY}"
        res_s = requests.get(url_s, timeout=3).json()
        if res_s.get("Response") == "True" and res_s.get("Search"):
            first_match = res_s["Search"][0]
            if first_match.get("Poster") and first_match["Poster"] != "N/A":
                return first_match["Poster"]
    except Exception:
        pass

    # 3. Fallback: Google Books (Pôsteres de filmes/séries famosos também estão no Google Books)
    backup_cover = get_book_cover(title_str)
    if "dummyimage.com" not in backup_cover:
        return backup_cover

    return generate_card_url(title_str, bg_color="1e1b4b" if "série" in str(media_type).lower() else "450a0a")

# --- CARREGAMENTO DE DADOS ---
@st.cache_data(ttl=300)
def load_data(sheet_name):
    try:
        gid = GIDS.get(sheet_name, "0")
        url = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/export?format=csv&gid={gid}"
        data = pd.read_csv(url, header=None)
        
        if sheet_name == "LIVROS":
            df = data.iloc[3:, [1, 2, 3, 4]].copy()
            df.columns = ["Título", "Autor", "Gênero", "Status"]
            df = df[df["Título"].fillna("").astype(str).str.strip() != ""]
            df = df[~df["Título"].astype(str).str.upper().isin(["TITULO", "TÍTULO"])]
            return df

        elif sheet_name == "SÉRIES":
            df = data.iloc[3:, [0, 1, 2, 3]].copy()
            df.columns = ["Série", "Temporada", "Streaming", "Status"]
            df["Série"] = df["Série"].replace("", None).ffill()
            df = df[df["Série"].fillna("").astype(str).str.strip() != ""]
            df = df[~df["Série"].astype(str).str.upper().isin(["SÉRIIE", "SÉRIE", "SERIE"])]
            return df

        elif sheet_name == "UNIVERSO MARVEL":
            df = data.iloc[4:, [0, 1, 2, 3]].copy()
            df.columns = ["Título", "Tipo", "Ano", "Status"]
            df = df[df["Título"].fillna("").astype(str).str.strip() != ""]
            df = df[~df["Título"].astype(str).str.upper().isin(["TITULO", "TÍTULO"])]
            return df

    except Exception as e:
        st.error(f"Erro ao carregar {sheet_name}: {e}")
        return pd.DataFrame()

# --- INTERFACE PRINCIPAL ---
st.title("🍿 Procrastinação Organizada")
st.caption("Seu Hub Pessoal de Entretenimento")

aba_livros, aba_series, aba_marvel = st.tabs(["📚 Biblioteca Virtual", "📺 Tracker de Séries", "🦸 Universo Marvel"])

# 1. LIVROS
with aba_livros:
    df_l = load_data("LIVROS")
    if not df_l.empty:
        lidos = len(df_l[df_l["Status"].astype(str).str.upper().str.strip() == "LIDO"])
        tot_l = len(df_l)
        pct_l = int((lidos / tot_l) * 100) if tot_l > 0 else 0
        
        st.subheader(f"Biblioteca Virtual: {lidos}/{tot_l} lidos ({pct_l}%)")
        st.progress(lidos / tot_l if tot_l > 0 else 0)
        st.divider()

        generos = ["Todos"] + [str(g) for g in df_l["Gênero"].dropna().unique() if str(g).strip()]
        gen_selected = st.selectbox("Filtrar por Gênero:", generos)
        if gen_selected != "Todos":
            df_l = df_l[df_l["Gênero"].astype(str) == gen_selected]

        itens_por_pagina = 24
        total_paginas = (len(df_l) - 1) // itens_por_pagina + 1 if len(df_l) > 0 else 1
        
        col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
        with col_p2:
            pagina = st.number_input("Página", min_value=1, max_value=total_paginas, value=1, step=1)
            st.caption(f"Mostrando página {pagina} de {total_paginas} (Total de {len(df_l)} livros)")

        inicio = (pagina - 1) * itens_por_pagina
        fim = inicio + itens_por_pagina
        df_pagina = df_l.iloc[inicio:fim]

        cols_l = st.columns(4)
        for idx, (_, row) in enumerate(df_pagina.iterrows()):
            with cols_l[idx % 4]:
                cover_url = get_book_cover(row["Título"], row["Autor"])
                st.image(cover_url, use_container_width=True)
                st.write(f"**#{inicio + idx + 1} - {row['Título']}**")
                st.caption(f"✍️ {row['Autor']} | 🏷️ {row['Gênero']}")
                is_lido = (str(row["Status"]).upper().strip() == "LIDO")
                st.checkbox("Lido", value=is_lido, key=f"livro_{inicio + idx}")
                st.markdown("---")

# 2. SÉRIES
with aba_series:
    df_s = load_data("SÉRIES")
    if not df_s.empty:
        fin = len(df_s[df_s["Status"].astype(str).str.upper().str.strip() == "FINALIZADA"])
        tot_s = len(df_s)
        pct_s = int((fin / tot_s) * 100) if tot_s > 0 else 0
        
        st.subheader(f"Progresso de Séries: {fin}/{tot_s} Temporadas Finalizadas ({pct_s}%)")
        st.progress(fin / tot_s if tot_s > 0 else 0)
        st.divider()

        series_unicas = df_s.drop_duplicates(subset=["Série"])

        cols_s = st.columns(4)
        for idx, (_, row) in enumerate(series_unicas.iterrows()):
            with cols_s[idx % 4]:
                poster_url = get_omdb_poster(row["Série"], media_type="series")
                st.image(poster_url, use_container_width=True)
                st.write(f"**#{idx+1} - {row['Série']}**")
                st.caption(f"📺 {row['Temporada']} | 🍿 {row['Streaming']}")
                is_finalizada = (str(row["Status"]).upper().strip() == "FINALIZADA")
                st.checkbox("Finalizada", value=is_finalizada, key=f"serie_{idx}")
                st.markdown("---")

# 3. UNIVERSO MARVEL
with aba_marvel:
    df_m = load_data("UNIVERSO MARVEL")
    if not df_m.empty:
        ass = len(df_m[df_m["Status"].astype(str).str.upper().str.strip() == "SIM"])
        tot_m = len(df_m)
        pct_m = int((ass / tot_m) * 100) if tot_m > 0 else 0
        
        st.subheader(f"Maratona MCU: {ass}/{tot_m} assistidos ({pct_m}%)")
        st.progress(ass / tot_m if tot_m > 0 else 0)
        st.divider()

        cols_m = st.columns(4)
        for idx, (_, row) in enumerate(df_m.iterrows()):
            with cols_m[idx % 4]:
                poster_url = get_omdb_poster(row["Título"], media_type=row["Tipo"])
                st.image(poster_url, use_container_width=True)
                st.write(f"**#{idx+1} - {row['Título']}**")
                st.caption(f"🎬 {row['Tipo']} | 📅 {row['Ano']}")
                is_checked = (str(row["Status"]).upper().strip() == "SIM")
                st.checkbox("Assistido", value=is_checked, key=f"mcu_{idx}")
                st.markdown("---")
