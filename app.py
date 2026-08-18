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

TMDB_API_KEY = "34cfcdc95d19256cbdef1189f11f556"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

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

FALLBACK_IMG = "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=400&q=80"

# --- BUSCA GOOGLE BOOKS ---
@st.cache_data(ttl=86400)
def get_book_cover(title, author=""):
    title_str = str(title).strip() if pd.notna(title) else ""
    if not title_str or title_str.lower() in ["nan", "none"]:
        return FALLBACK_IMG
    
    try:
        query = f"{title_str} {author}".strip()
        url = f"https://www.googleapis.com/books/v1/volumes?q={urllib.parse.quote(query)}&maxResults=1"
        res = requests.get(url, headers=HEADERS, timeout=4).json()
        if "items" in res and len(res["items"]) > 0:
            links = res["items"][0].get("volumeInfo", {}).get("imageLinks", {})
            cover = links.get("thumbnail") or links.get("smallThumbnail")
            if cover:
                return cover.replace("http://", "https://")
    except Exception:
        pass
        
    return FALLBACK_IMG

# --- BUSCA TMDB COM DUAL SEARCH (FILME + TV) ---
@st.cache_data(ttl=86400)
def get_tmdb_poster(title, media_type="movie"):
    title_str = str(title).strip() if pd.notna(title) else ""
    if not title_str or title_str.lower() in ["nan", "none"]:
        return FALLBACK_IMG
    
    # 1. Tenta buscar no TMDB
    try:
        type_clean = str(media_type).lower().strip()
        search_type = "tv" if any(x in type_clean for x in ["série", "serie", "tv"]) else "movie"
        encoded = urllib.parse.quote(title_str)
        
        # Tentativa 1: Busca no tipo especificado
        url = f"https://api.themoviedb.org/3/search/{search_type}?api_key={TMDB_API_KEY}&query={encoded}&language=pt-BR"
        res = requests.get(url, headers=HEADERS, timeout=4).json()
        
        if "results" in res and len(res["results"]) > 0:
            poster_path = res["results"][0].get("poster_path")
            if poster_path:
                return f"https://image.tmdb.org/t/p/w500{poster_path}"

        # Tentativa 2: Se falhar (ex: marcou filme mas era série), tenta o outro tipo
        alt_type = "movie" if search_type == "tv" else "tv"
        url_alt = f"https://api.themoviedb.org/3/search/{alt_type}?api_key={TMDB_API_KEY}&query={encoded}&language=pt-BR"
        res_alt = requests.get(url_alt, headers=HEADERS, timeout=4).json()
        if "results" in res_alt and len(res_alt["results"]) > 0:
            poster_path = res_alt["results"][0].get("poster_path")
            if poster_path:
                return f"https://image.tmdb.org/t/p/w500{poster_path}"
    except Exception:
        pass

    # 2. Se o TMDB falhar, usa o Google Books como backup de imagem
    backup_cover = get_book_cover(title_str)
    if backup_cover != FALLBACK_IMG:
        return backup_cover

    return FALLBACK_IMG

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
                poster_url = get_tmdb_poster(row["Série"], media_type="tv")
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
                poster_url = get_tmdb_poster(row["Título"], media_type=row["Tipo"])
                st.image(poster_url, use_container_width=True)
                st.write(f"**#{idx+1} - {row['Título']}**")
                st.caption(f"🎬 {row['Tipo']} | 📅 {row['Ano']}")
                is_checked = (str(row["Status"]).upper().strip() == "SIM")
                st.checkbox("Assistido", value=is_checked, key=f"mcu_{idx}")
                st.markdown("---")
