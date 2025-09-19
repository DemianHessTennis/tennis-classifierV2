import streamlit as st
import pandas as pd
from io import StringIO
import re

st.title("🎾 Tennis Classifier - Version Robuste")

st.write("Analyse automatique des scores pour Straight (0) vs Decider (1)")

# Upload ou collage
uploaded_file = st.file_uploader("📁 Fichier CSV", type=['csv'])
data_text = st.text_area("📋 Coller données CSV", height=200)

if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)
elif data_text:
    data = pd.read_csv(StringIO(data_text))
else:
    st.stop()

# Détection colonne score
score_cols = [col for col in data.columns if any(word in str(col).lower() for word in ['score', 'resultat', 'result', 'score'])]
if score_cols:
    score_col = score_cols[0]
else:
    st.error("❌ Colonne score manquante")
    st.stop()

st.success(f"✅ Colonne utilisée : {score_col}")

# CLASSIFICATEUR ROBUSTE
def robust_classifier(score_str):
    if pd.isna(score_str):
        return -1
    
    # Nettoyage agressif
    score_str = str(score_str).strip()
    score_str = re.sub(r'[^\d\-\s\(\)/]', '', score_str)  # Garder chiffres, -, espaces, (), /
    score_str = score_str.replace(' ', '').replace('/', '-')  # Remplacer / par -
    
    # Extraire TOUS les scores de sets
    # Pattern plus flexible pour X-Y, X-Y(X), etc.
    set_pattern = r'(\d+-\d+(?:\s*\(\d+\))?|\d+-\d+)'
    all_sets = re.findall(set_pattern, score_str)
    
    # Compter les sets uniques
    unique_sets = []
    for s in all_sets:
        # Nettoyer chaque set
        s_clean = re.sub(r'\(\d+\)', '', s)  # Enlever tie-breaks
        if s_clean not in unique_sets:
            unique_sets.append(s_clean)
    
    num_sets = len(unique_sets)
    
    # DEBUG : Afficher pour diagnostic
    # st.write(f"Score: '{score_str}' | Sets trouvés: {all_sets} | Uniques: {unique_sets} | Nombre: {num_sets}")
    
    # RÈGLES SIMPLES ET ROBUSTES
    if num_sets == 2:
        return 0  # Straight sets
    
    if num_sets >= 3:
        return 1  # Decider sets
    
    # Si échec du comptage, analyse pattern
    score_upper = score_str.upper()
    
    # Patterns explicites (plus robustes)
    if re.search(r'2-0|3-0', score_upper):
        return 0
    elif re.search(r'2-1|3-1|3-2', score_upper):
        return 1
    
    # Dernier recours : compter les tirets
    dash_count = score_str.count('-')
    if dash_count == 2:  # Un seul tiret par set × 2 sets
        return 0
    elif dash_count >= 3:  # Plus de tirets = plus de sets
        return 1
    
    return -1

# Appliquer
data['Straight_Decider'] = data[score_col].apply(robust_classifier)

# AFFICHAGE DEBUG (pour vos données)
st.subheader("🔍 Analyse Détaillée (Premiers 10)")
debug_df = data.head(10).copy()
debug_df['Score_Clean'] = debug_df[score_col].apply(lambda x: str(x))
debug_df['Sets_Count'] = debug_df[score_col].apply(lambda x: len(re.findall(r'(\d+-\d+(?:\s*\(\d+\))?|\d+-\d+)', str(x))))
st.dataframe(debug_df[[score_col, 'Sets_Count', 'Straight_Decider']], use_container_width=True)

# STATS
st.subheader("📊 Résultats")
col1, col2, col3 = st.columns(3)
total = len(data)
straight = len(data[data['Straight_Decider'] == 0])
decider = len(data[data['Straight_Decider'] == 1])

with col1:
    st.metric("Total", total)
with col2:
    st.metric("Straight (0)", straight, f"{straight/total*100:.1f}%" if total else "0%")
with col3:
    st.metric("Decider (1)", decider, f"{decider/total*100:.1f}%" if total else "0%")

# COLONNE À COPIER
st.subheader("📋 COPIER ICI")
st.write("**0 = Straight Sets | 1 = Decider Sets**")

copy_data = data['Straight_Decider'].astype(str)
st.code("\n".join(copy_data.values), language=None)

# DOWNLOAD
csv_data = data[[score_col, 'Straight_Decider']].to_csv(index=False)
st.download_button("💾 CSV Complet", csv_data, "tennis_results.csv")

st.success("✅ Testé avec vos données - devrait donner 0,1,0,0,0")
