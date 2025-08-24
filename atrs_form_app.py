#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ATSR – Formulário individual por integrante (Streamlit)
------------------------------------------------------
• Cada pessoa escolhe seu nome e avalia apenas os 3 colegas do próprio subgrupo.
• 5 critérios (0–10) por avaliado.
• Ao enviar, salva em CSV (append) e mostra mensagem de sucesso.
• Inclui **Painel do Organizador** para visualizar e **baixar** os resultados consolidados (ATSR por pessoa, ranking por subgrupo/geral, CSV e XLSX).

Como executar localmente (com Python instalado):
    pip install streamlit pandas openpyxl
    streamlit run atrs_form_app.py

Como empacotar em .EXE (Windows) para quem não tem VS Code / Python:
    pip install pyinstaller
    pyinstaller --onefile --add-data "atrs_form_app.py;." --name ATRS_Form atrs_form_app.py
(Depois, execute o ATRS_Form.exe gerado em dist/.)
"""

from __future__ import annotations
import streamlit as st
from datetime import datetime
import csv
from pathlib import Path
import io
import pandas as pd

st.set_page_config(page_title="ATSR – Sprint Regular", page_icon="✅", layout="centered")

# ===================== CONFIG ===================== #
ARQUIVO_SAIDA = Path("respostas_ATSR.csv")
CRITERIOS = [
    "Comunicação",
    "Eficiência durante o processo",
    "Participação e presença",
    "Processo criativo e insights",
    "Responsabilidade e precedência",
]
SUBGRUPOS = {
    "Subgrupo 01": ["Artur Prazeres", "Filipe Correia", "Thiago Carvalho", "Walter Maia"],
    "Subgrupo 02": ["João Carlos", "João Patriota", "João Pessôa", "Mateus Dornellas"],
    "Subgrupo 03": ["Antônio Manoel", "Breno Santiago", "Gabriel Ribeiro", "João Henrique"],
}
TODOS_NOMES = sum(SUBGRUPOS.values(), [])
SENHA_ORGANIZADOR = "organizador"  # altere aqui se quiser

# ===================== HELPERS ===================== #

def get_subgrupo_do_nome(nome: str) -> str | None:
    for sg, nomes in SUBGRUPOS.items():
        if nome in nomes:
            return sg
    return None

@st.cache_data
def cabecalho_csv() -> list[str]:
    return [
        "timestamp",
        "avaliador_nome",
        "avaliador_subgrupo",
        "avaliado_nome",
        *CRITERIOS,
        "media_5_criterios",
    ]


def salvar_linha_csv(linha: list[str | float]) -> None:
    novo_arquivo = not ARQUIVO_SAIDA.exists()
    with ARQUIVO_SAIDA.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if novo_arquivo:
            writer.writerow(cabecalho_csv())
        writer.writerow(linha)


def bloco_avaliacao(avaliador_nome: str, avaliado_nome: str) -> float:
    st.subheader(f"Avaliar: {avaliado_nome}")
    notas = {}
    for criterio in CRITERIOS:
        # Slider (0–10). Pode ajustar step para 0.5 se preferir.
        notas[criterio] = st.slider(
            criterio,
            min_value=0.0,
            max_value=10.0,
            value=5.0,
            step=0.5,
            key=f"{avaliador_nome}->{avaliado_nome}:{criterio}",
        )
    media = sum(notas.values()) / len(notas)
    st.caption(f"Média (5 critérios) de {avaliado_nome}: **{media:.2f}**")

    # Guardar temporário no session_state
    st.session_state.setdefault("avaliacoes", {})
    st.session_state["avaliacoes"][avaliado_nome] = notas
    return media

# ===================== PÁGINAS ===================== #

def pagina_avaliador():
    st.markdown("""
    # ✅ ATSR – Sprint Regular (Formulário)
    Escolha seu nome e avalie **apenas os colegas do seu subgrupo**.
    Cada avaliação tem **5 critérios** (0–10). Ao enviar, as respostas são salvas e você pode fechar.
    """)

    avaliador_nome = st.selectbox("Quem é você?", ["— selecione —"] + TODOS_NOMES)

    if not avaliador_nome or avaliador_nome == "— selecione —":
        st.info("Selecione seu nome para começar.")
        return

    subgrupo = get_subgrupo_do_nome(avaliador_nome)
    if not subgrupo:
        st.error("Nome não mapeado em nenhum subgrupo. Procure o organizador.")
        return

    st.success(f"Você está em **{subgrupo}**")

    # Colegas a avaliar (mesmo subgrupo, exclui o próprio nome)
    colegas = [n for n in SUBGRUPOS[subgrupo] if n != avaliador_nome]

    st.divider()
    st.markdown("### Avaliações deste sprint")

    for colega in colegas:
        bloco_avaliacao(avaliador_nome, colega)
        st.divider()

    if st.button("Enviar minhas avaliações", type="primary"):
        faltando = [c for c in colegas if c not in st.session_state.get("avaliacoes", {})]
        if faltando:
            st.warning("Finalize todas as avaliações antes de enviar.")
            return

        ts = datetime.now().isoformat(timespec="seconds")
        for colega in colegas:
            notas = st.session_state["avaliacoes"][colega]
            media = sum(notas.values()) / len(notas)
            linha = [
                ts,
                avaliador_nome,
                subgrupo,
                colega,
                *[notas[c] for c in CRITERIOS],
                f"{media:.2f}",
            ]
            salvar_linha_csv(linha)

        st.balloons()
        st.success("Avaliação feita com sucesso! Você já pode fechar o aplicativo.")
        # Evitar reenvio acidental
        st.session_state["avaliacoes"] = {}


def carregar_dataframe() -> pd.DataFrame | None:
    if not ARQUIVO_SAIDA.exists():
        return None
    df = pd.read_csv(ARQUIVO_SAIDA)
    return df


def consolidar_atrs(df: pd.DataFrame) -> pd.DataFrame:
    # ATSR por avaliado = média das médias (media_5_criterios) de todos os avaliadores
    df['media_5_criterios'] = pd.to_numeric(df['media_5_criterios'], errors='coerce')
    resumo = (df.groupby('avaliado_nome', as_index=False)
                .agg(ATSR=('media_5_criterios', 'mean')))
    # Adiciona subgrupo do avaliado
    def subgrupo_avaliado(nome):
        return next((sg for sg, nomes in SUBGRUPOS.items() if nome in nomes), '—')
    resumo['Subgrupo'] = resumo['avaliado_nome'].apply(subgrupo_avaliado)
    cols = ['Subgrupo', 'avaliado_nome', 'ATSR']
    resumo = resumo[cols].rename(columns={'avaliado_nome': 'Integrante'})
    resumo['ATSR'] = resumo['ATSR'].round(2)
    return resumo


def baixar_arquivo_bytes(df: pd.DataFrame, formato: str = 'csv') -> bytes:
    if formato == 'csv':
        return df.to_csv(index=False).encode('utf-8')
    elif formato == 'xlsx':
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='ATSR')
        buf.seek(0)
        return buf.read()
    else:
        return b''


def pagina_organizador():
    st.markdown("""
    # 🧭 Painel do Organizador
    Aqui você vê os envios, consolida o **ATSR** por pessoa, gera **ranking** por subgrupo e geral,
    e pode **baixar** os resultados em CSV/XLSX.
    """)

    senha = st.text_input("Senha do organizador", type="password")
    if senha != SENHA_ORGANIZADOR:
        st.info("Digite a senha para acessar o painel.")
        return

    df = carregar_dataframe()
    if df is None or df.empty:
        st.warning("Ainda não há respostas salvas (respostas_ATSR.csv).")
        return

    st.subheader("📥 Respostas brutas")
    st.dataframe(df, use_container_width=True)
    st.download_button(
        "Baixar respostas (CSV)",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name='respostas_ATSR.csv',
        mime='text/csv',
    )

    st.divider()
    st.subheader("📊 Consolidação – ATSR por integrante")
    resumo = consolidar_atrs(df)

    # Ranking por subgrupo
    for sg in SUBGRUPOS.keys():
        st.markdown(f"### {sg}")
        sub = resumo[resumo['Subgrupo'] == sg].sort_values('ATSR', ascending=False)
        st.dataframe(sub, use_container_width=True)

    st.markdown("### 🔝 Ranking Geral")
    geral = resumo.sort_values(['ATSR', 'Subgrupo', 'Integrante'], ascending=[False, True, True]).reset_index(drop=True)
    geral.index = geral.index + 1
    st.dataframe(geral, use_container_width=True)

    # Downloads
    st.download_button(
        "Baixar consolidação (CSV)",
        data=baixar_arquivo_bytes(resumo, 'csv'),
        file_name='ATSR_consolidado.csv',
        mime='text/csv',
    )
    st.download_button(
        "Baixar consolidação (XLSX)",
        data=baixar_arquivo_bytes(resumo, 'xlsx'),
        file_name='ATSR_consolidado.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )

# ===================== ROTEAMENTO ===================== #

modo = st.sidebar.radio("Modo", ["Avaliador", "Organizador"], index=0)
if modo == "Avaliador":
    pagina_avaliador()
else:
    pagina_organizador()
