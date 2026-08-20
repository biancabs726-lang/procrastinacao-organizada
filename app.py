import streamlit as st
import pandas as pd
import requests
import urllib.parse
import re

# ID da Planilha e GIDs
DOC_ID = "1Dq9BXjt9tbsdFQryC3NBYJTXvhHjZbtEGdG_ZXpWdp0"

GIDS = {
    "LIVROS": "1591861167",
    "SÉRIES": "1513581778",
    "UNIVERSO MARVEL": "1360927897"
}

st.set_page_config(
    page_title="Procrastinação Organizada",
    page_icon="🍿",
    layout="wide"
)

# Estilização CSS: Tema Claro, Cards Limpos, Pesquisa Transparente e Barra Verde
st.markdown("""
<style>
    /* Fundo Claro Principal */
    .stApp { 
        background-color: #ffffff !important; 
        color: #1e293b !important; 
    }
    h1, h2, h3, h4, label, p, span { 
        color: #0f172a !important; 
    }
    
    /* Barra de Progresso Verde Padrão */
    .stProgress > div > div > div > div { 
        background-color: #22c55e !important; 
    }
    
    /* Pôsteres e Capas (85px x 130px) */
    div[data-testid="stImage"] img {
        border-radius: 6px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1) !important;
        object-fit: cover !important;
        height: 130px !important;
        width: 85px !important;
    }

    /* Botão do PDF */
    .pdf-btn {
        display: inline-block;
        padding: 4px 8px;
        background-color: #ef4444;
        color: #ffffff !important;
        border-radius: 4px;
        text-decoration: none;
        font-size: 11px;
        font-weight: 600;
        margin-top: 4px;
        margin-bottom: 4px;
    }
    .pdf-btn:hover {
        background-color: #dc2626;
    }

    /* Barra de Pesquisa Compacta e Transparente */
    div[data-testid="stTextInput"] {
        max-width: 320px !important;
    }
    div[data-testid="stTextInput"] > div > div {
        background-color: transparent !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px !important;
        color: #0f172a !important;
    }

    /* Botão de Adicionar Pequeno */
    button[kind="secondaryFormSubmit"], div[data-testid="stPopover"] button {
        font-size: 12px !important;
        padding: 2px 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# BUSCADOR DE CAPAS EM NUVEM
@st.cache_data(ttl=86400)
def fetch_online_poster(title_text):
    clean_title = re.sub(r'[^\w\s]', '', str(title_text)).replace("**", "").strip()
    if not clean_title or clean_title.lower() in ["nan", "none"]:
        return "https://via.placeholder.com/150x225/f1f5f9/475569?text=Sem+Capa"

    # 1. Google Books API
    try:
        url_gb = f"https://www.googleapis.com/books/v1/volumes?q={urllib.parse.quote(clean_title)}&maxResults=1"
        res_gb = requests.get(url_gb, timeout=2).json()
        if "items" in res_gb and len(res_gb["items"]) > 0:
            links = res_gb["items"][0].get("volumeInfo", {}).get("imageLinks", {})
            cover = links.get("thumbnail") or links.get("smallThumbnail")
            if cover:
                return cover.replace("http://", "https://")
    except Exception:
        pass

    # 2. Open Library API
    try:
        url_ol = f"https://openlibrary.org/search.json?title={urllib.parse.quote(clean_title)}"
        res_ol = requests.get(url_ol, timeout=2).json()
        if res_ol.get("docs") and len(res_ol["docs"]) > 0:
            cover_i = res_ol["docs"][0].get("cover_i")
            if cover_i:
                return f"https://covers.openlibrary.org/b/id/{cover_i}-M.jpg"
    except Exception:
        pass

    encoded = urllib.parse.quote(clean_title[:15])
    return f"https://via.placeholder.com/150x225/f1f5f9/475569?text={encoded}"

# CARREGAMENTO DE DADOS DIRETO DA PLANILHA GOOGLE
@st.cache_data(ttl=60)
def load_data(sheet_name):
    try:
        gid = GIDS.get(sheet_name, "0")
        url = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/export?format=csv&gid={gid}"
        df = pd.read_csv(url, header=None)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar {sheet_name}: {e}")
        return pd.DataFrame()

# INTERFACE PRINCIPAL
st.title("🍿 Procrastinação Organizada")
st.caption("Seu Hub Pessoal de Entretenimento")

aba_livros, aba_series, aba_marvel = st.tabs(["📚 Biblioteca Virtual", "📺 Tracker de Séries", "🦸 Universo Marvel"])

# 1. BIBLIOTECA VIRTUAL (LIVROS)
with aba_livros:
    data_l = load_data("LIVROS")
    if not data_l.empty:
        df_l = data_l.iloc[3:].copy().dropna(how="all")
        
        # Mapeamento de Colunas: [0: Capa/PDF, 1: Título, 2: Autor, 3: Gênero, 4: Status]
        cols_count = df_l.shape[1]
        if cols_count >= 5:
            df_l = df_l.iloc[:, [0, 1, 2, 3, 4]]
        else:
            df_l = df_l.iloc[:, [0, 1, 2, 3]]
            df_l[4] = "NÃO LIDO"

        df_l.columns = ["Link_Capa_PDF", "Título", "Autor", "Gênero", "Status"]
        df_l = df_l[df_l["Título"].fillna("").astype(str).str.strip() != ""]
        df_l = df_l[~df_l["Título"].astype(str).str.upper().isin(["TITULO", "TÍTULO"])]

        lidos = len(df_l[df_l["Status"].astype(str).str.upper().str.strip() == "LIDO"])
        tot_l = len(df_l)
        pct_l = int((lidos / tot_l) * 100) if tot_l > 0 else 0
        
        st.subheader(f"Biblioteca Virtual: {lidos}/{tot_l} lidos ({pct_l}%)")
        st.progress(lidos / tot_l if tot_l > 0 else 0)

        # Botão Pequeno de Adicionar
        with st.popover("➕ Adicionar Livro"):
            st.write("**Cadastrar Livro**")
            novo_pdf = st.text_input("Link do PDF no Google Drive", key="add_l_pdf")
            novo_titulo = st.text_input("Título", key="add_l_title")
            novo_autor = st.text_input("Autor", key="add_l_author")
            novo_genero = st.text_input("Gênero", key="add_l_gen")
            novo_status = st.selectbox("Status", ["LIDO", "NÃO LIDO"], key="add_l_status")
            if st.button("Salvar Livro", key="btn_salvar_l"):
                st.cache_data.clear()
                st.success("Salvo com sucesso!")
                st.rerun()

        # Filtros e Pesquisa Compacta
        col_f1, col_f2 = st.columns([1, 2])
        with col_f1:
            generos = ["Todos"] + [str(g) for g in df_l["Gênero"].dropna().unique() if str(g).strip()]
            gen_selected = st.selectbox("Gênero:", generos, key="gen_l")
        with col_f2:
            search_l = st.text_input("🔍 Pesquisar...", key="search_l")

        if gen_selected != "Todos":
            df_l = df_l[df_l["Gênero"].astype(str) == gen_selected]
        if search_l:
            df_l = df_l[df_l["Título"].astype(str).str.contains(search_l, case=False, na=False)]

        # Paginação
        itens_por_pagina = 20
        total_paginas = (len(df_l) - 1) // itens_por_pagina + 1 if len(df_l) > 0 else 1
        
        col_p1, col_p2 = st.columns([1, 3])
        with col_p1:
            pagina = st.number_input("Página", min_value=1, max_value=total_paginas, value=1, step=1, key="pag_l")
        with col_p2:
            st.caption(f"Página {pagina} de {total_paginas} ({len(df_l)} livros)")

        inicio = (pagina - 1) * itens_por_pagina
        df_pagina = df_l.iloc[inicio:inicio + itens_por_pagina]

        st.divider()

        cols = st.columns(2)
        for idx, (_, row) in enumerate(df_pagina.iterrows()):
            with cols[idx % 2]:
                c1, c2 = st.columns([1, 4])
                
                link_val = str(row.get("Link_Capa_PDF", "")).strip()
                has_pdf_link = any(k in link_val.lower() for k in ["http", "drive.google.com", "docs.google.com", ".pdf"])
                
                with c1:
                    if has_pdf_link and any(ext in link_val.lower() for ext in [".jpg", ".png", ".jpeg", ".webp"]):
                        img_url = link_val
                    else:
                        img_url = fetch_online_poster(row["Título"])
                    st.image(img_url)
                with c2:
                    st.write(f"**#{inicio + idx + 1} - {row['Título']}**")
                    st.caption(f"✍️ {row['Autor']} | 🏷️ {row['Gênero']}")
                    
                    if has_pdf_link:
                        st.markdown(f'<a href="{link_val}" target="_blank" class="pdf-btn">📄 Abrir PDF no Drive</a>', unsafe_allow_html=True)
                    
                    is_lido = (str(row["Status"]).upper().strip() == "LIDO")
                    st.checkbox("Lido", value=is_lido, key=f"livro_{inicio + idx}")
                st.markdown("---")

# 2. TRACKER DE SÉRIES (COMPACTADO COM MENU SUSPENSO DE TEMPORADAS)
with aba_series:
    data_s = load_data("SÉRIES")
    if not data_s.empty:
        df_s = data_s.iloc[3:, [0, 1, 2, 3]].copy()
        df_s.columns = ["Série", "Temporada", "Streaming", "Status"]
        df_s["Série"] = df_s["Série"].replace("", None).ffill()
        df_s = df_s[df_s["Série"].fillna("").astype(str).str.strip() != ""]
        df_s = df_s[~df_s["Série"].astype(str).str.upper().isin(["SÉRIIE", "SÉRIE", "SERIE"])]

        fin = len(df_s[df_s["Status"].astype(str).str.upper().str.strip() == "FINALIZADA"])
        tot_s = len(df_s)
        pct_s = int((fin / tot_s) * 100) if tot_s > 0 else 0
        
        st.subheader(f"Progresso de Séries: {fin}/{tot_s} Temporadas Finalizadas ({pct_s}%)")
        st.progress(fin / tot_s if tot_s > 0 else 0)

        with st.popover("➕ Adicionar Série"):
            st.write("**Cadastrar Série**")
            nova_serie = st.text_input("Nome da Série", key="add_s_title")
            nova_temp = st.text_input("Temporada", key="add_s_temp")
            novo_stream = st.text_input("Streaming", key="add_s_stream")
            novo_s_status = st.selectbox("Status", ["FINALIZADA", "EM ANDAMENTO", "NÃO INICIADO"], key="add_s_status")
            if st.button("Salvar Série", key="btn_salvar_s"):
                st.cache_data.clear()
                st.success("Salvo com sucesso!")
                st.rerun()

        search_s = st.text_input("🔍 Pesquisar...", key="search_s")
        
        if search_s:
            df_s = df_s[df_s["Série"].astype(str).str.contains(search_s, case=False, na=False)]

        st.divider()

        # Agrupamento Mantendo Ordem Original da Planilha
        grouped_series = df_s.groupby("Série", sort=False)
        series_list = list(grouped_series)

        cols_s = st.columns(2)
        for idx, (nome_serie, grupo) in enumerate(series_list):
            clean_s_title = str(nome_serie).replace("**", "").strip()
            streaming_info = grupo["Streaming"].dropna().iloc[0] if not grupo["Streaming"].dropna().empty else "Streaming"
            
            with cols_s[idx % 2]:
                c1, c2 = st.columns([1, 4])
                with c1:
                    poster_url = fetch_online_poster(clean_s_title)
                    st.image(poster_url)
                with c2:
                    st.write(f"**#{idx+1} - {clean_s_title}**")
                    st.caption(f"🍿 {streaming_info}")
                    
                    # Menu Suspenso de Temporadas
                    temp_opcoes = [f"{row['Temporada']}" for _, row in grupo.iterrows()]
                    temp_selecionada = st.selectbox("Temporada:", temp_opcoes, key=f"select_temp_{idx}")
                    
                    # Status da Temporada Selecionada
                    row_selecionada = grupo[grupo["Temporada"].astype(str) == temp_selecionada.split(" - ")[-1]].iloc[0] if temp_selecionada in grupo["Temporada"].values else grupo.iloc[0]
                    status_atual = str(row_selecionada["Status"]).upper().strip()
                    
                    opcoes_status = ["NÃO INICIADO", "EM ANDAMENTO", "FINALIZADA"]
                    index_status = opcoes_status.index(status_atual) if status_atual in opcoes_status else 0
                    
                    st.radio("Status da Temporada:", opcoes_status, index=index_status, key=f"status_temp_{idx}", horizontal=True)

                st.markdown("---")

# 3. UNIVERSO MARVEL
with aba_marvel:
    data_m = load_data("UNIVERSO MARVEL")
    if not data_m.empty:
        df_m = data_m.iloc[4:, [0, 1, 2, 3]].copy()
        df_m.columns = ["Título", "Tipo", "Ano", "Status"]
        df_m = df_m[df_m["Título"].fillna("").astype(str).str.strip() != ""]
        df_m = df_m[~df_m["Título"].astype(str).str.upper().isin(["TITULO", "TÍTULO"])]

        ass = len(df_m[df_m["Status"].astype(str).str.upper().str.strip() == "SIM"])
        tot_m = len(df_m)
        pct_m = int((ass / tot_m) * 100) if tot_m > 0 else 0
        
        st.subheader(f"Maratona MCU: {ass}/{tot_m} assistidos ({pct_m}%)")
        st.progress(ass / tot_m if tot_m > 0 else 0)

        with st.popover("➕ Adicionar Marvel"):
            st.write("**Cadastrar no MCU**")
            novo_m_title = st.text_input("Título", key="add_m_title")
            novo_m_tipo = st.selectbox("Tipo", ["FILME", "SÉRIE"], key="add_m_tipo")
            novo_m_ano = st.text_input("Ano / Período", key="add_m_ano")
            novo_m_status = st.selectbox("Assistido?", ["SIM", "NÃO"], key="add_m_status")
            if st.button("Salvar Marvel", key="btn_salvar_m"):
                st.cache_data.clear()
                st.success("Salvo com sucesso!")
                st.rerun()

        search_m = st.text_input("🔍 Pesquisar...", key="search_m")
        if search_m:
            df_m = df_m[df_m["Título"].astype(str).str.contains(search_m, case=False, na=False)]

        st.divider()

        cols_m = st.columns(2)
        for idx, (_, row) in enumerate(df_m.iterrows()):
            with cols_m[idx % 2]:
                c1, c2 = st.columns([1, 4])
                clean_m_title = str(row["Título"]).replace("**", "").strip()
                with c1:
                    poster_url = fetch_online_poster(clean_m_title)
                    st.image(poster_url)
                with c2:
                    st.write(f"**#{idx+1} - {clean_m_title}**")
                    st.caption(f"🎬 {row['Tipo']} | 📅 {row['Ano']}")
                    is_checked = (str(row["Status"]).upper().strip() == "SIM")
                    st.checkbox("Assistido", value=is_checked, key=f"mcu_{idx}")
                st.markdown("---")
