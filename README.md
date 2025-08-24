# 📊 ATSR – Sprint Regular Form

Formulário interativo em **Streamlit** para avaliação de sprints de equipes.  
Cada integrante avalia apenas os colegas do próprio subgrupo em 5 critérios:

1. Comunicação  
2. Eficiência durante o processo  
3. Participação e presença  
4. Processo criativo e insights  
5. Responsabilidade e precedência  

As notas são salvas em um CSV (`respostas_ATSR.csv`).  
O aplicativo também inclui um **Painel do Organizador**, com ranking por subgrupo, ranking geral e exportação em CSV/XLSX.

---

## 🚀 Como executar localmente

### Pré-requisitos
- Python 3.9 ou superior
- Pip atualizado (`python -m pip install --upgrade pip`)

### Instalação
```bash
pip install streamlit pandas openpyxl
