import streamlit as st
import pandas as pd
from io import StringIO
import re

st.title("🎾 Tennis Classifier - Version Robuste")

st.write("Analyse automatique des scores pour Straight (0) vs Decider (1), avec détection Grand Chelem (BO5)")

# Upload ou collage
uploaded_file = st.file_uploader("📁 Fichier CSV", type=['csv'])
data_text = st.text_area("📋 Coller données CSV", height=200)

if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)
elif data_text:
    data = pd.read_csv(StringIO(data_text))
else:
    st.stop()

# 🔹 Correction: rendre les colonnes uniques si doublons
if data.columns.duplicated().any():
    data.columns = pd.io.parsers.ParserBase({'names': data.columns})._maybe_dedup_names(data.columns)

# Détection colonne score
score_cols = [col for col in data.columns if any(word in str(col).lower() for word in ['score', 'resultat', 'result'])]
if score_cols:
    score_col = score_cols[0]
else:
    st.error("❌ Colonne score manquante")
    st.stop()

st.success(f"✅ Colonne utilisée : {score_col}")

# Tournois en best-of-5
grand_slam_names = ['Australian Open', 'Roland Garros', 'Wimbledon', 'US Open']

# Détection de la colonne tournoi
tournament_cols = [col for col in data.columns if any(word in str(col).lower() for word in ['tournament', 'event', 'tournoi'])]
if tournament_cols:
    tournament_col = tournament_cols[0]
    st.success(f"✅ Colonne tournoi détectée : {tournament_col}")
else:
    tournament_col = None
    st.warning("⚠️ Colonne tournoi non détectée automatiquement.")

# CLASSIFICATEUR ROBUSTE AVEC CONTEXTE GRAND CHELEM
def robust_classifier(score_str, tournament_name=None):
    if pd.isna(score_str):
        return -1

    # Nettoyage agressif
    score_str = str(score_str).strip()
    score_str = re.sub(r'[^\d\-\s\(\)/]', '', score_str)
    score_str = score_str.replace(' ', '').replace('/', '-')

    # Extraction des sets
    set_pattern = r'(\d+-\d+(?:\s*\(\d+\))?|\d+-\d+)'
    all_sets = re.findall(set_pattern, score_str)

    # Nettoyer et compter sets uniques
    unique_sets = []
    for s in all_sets:
        s_clean = re.sub(r'\(\d+\)', '', s)
        if s_clean not in unique_sets:
            unique_sets.append(s_clean)

    num_sets = len(unique_sets)
    is_grand_slam = tournament_name in grand_slam_names if tournament_name else False

    # 🔹 Règle explicite Grand Chelem BO5
    if is_grand_slam:
        if num_sets in [3, 4]:
            return 0  # Straight sets
        elif num_sets == 5:
            return 1  # Decider
        else:
            return -1

    # 🔹 Tournois classiques BO3
    else:
        if num_sets == 2:
            return 0  # Straight sets
        elif num_sets == 3:
            return 1  # Decider
        else:
            return -1

# Appliquer classifier avec ou sans tournoi
if tournament_col:
    data['Straight_Decider'] = data.apply(
        lambda row: robust_classifier(row[score_col], row[tournament_col]), axis=1
    )
else:
    data['Straight_Decider'] = data[score_col].apply(robust_classifier)

# AFFICHAGE DEBUG
st.subheader("🔍 Analyse Détaillée (Premiers 10)")
debug_df = data.head(10).copy()
debug_df['Score_Clean'] = debug_df[score_col].apply(lambda x: str(x))
debug_df['Sets_Count'] = debug_df[score_col].apply(
    lambda x: len(re.findall(r'(\d+-\d+(?:\s*\(\d+\))?|\d+-\d+)', str(x)))
)

# 🔹 Correction : éviter doublons
display_cols = list(dict.fromkeys([score_col] + ([tournament_col] if tournament_col else []) + ['Sets_Count', 'Straight_Decider']))
st.dataframe(debug_df[display_cols], use_container_width=True)

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

st.success("✅ Analyse terminée.")
