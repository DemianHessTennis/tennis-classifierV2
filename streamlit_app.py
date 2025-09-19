import streamlit as st
import pandas as pd
from io import StringIO
import re

st.title("🎾 Tennis Classifier - Version Robuste")

st.write("Analyse automatique des scores pour Straight (0) vs Decider (1), avec détection Grand Chelem (BO5)")

# --- Upload ou collage ---
uploaded_file = st.file_uploader("📁 Fichier CSV", type=['csv'])
data_text = st.text_area("📋 Coller données CSV", height=200)

if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)
elif data_text:
    data = pd.read_csv(StringIO(data_text))
else:
    st.stop()

# --- Détection colonne score ---
score_cols = [col for col in data.columns if any(word in str(col).lower() for word in ['score', 'resultat', 'result'])]
if score_cols:
    score_col = score_cols[0]
else:
    st.error("❌ Colonne score manquante")
    st.stop()

st.success(f"✅ Colonne utilisée : {score_col}")

# --- Tournois en best-of-5 ---
grand_slam_names = ['Australian Open', 'Roland Garros', 'Wimbledon', 'US Open']

# --- Détection colonne tournoi ---
tournament_cols = [col for col in data.columns if any(word in str(col).lower() for word in ['tournament', 'event', 'tournoi'])]
if tournament_cols:
    tournament_col = tournament_cols[0]
    st.success(f"✅ Colonne tournoi détectée : {tournament_col}")
else:
    tournament_col = None
    st.warning("⚠️ Colonne tournoi non détectée automatiquement.")

# --- CLASSIFICATEUR ROBUSTE ---
def robust_classifier(score_str, tournament_name=None):
    if pd.isna(score_str):
        return -1

    # Nettoyage plus doux : garder chiffres, tirets, espaces, parenthèses
    score_str = str(score_str).strip()
    score_str = re.sub(r'[^0-9\-\s\(\)]', '', score_str)

    # Extraire les sets : ex. 7-6(5), 6-3, 0-6
    set_pattern = r'\d+-\d+(?:\(\d+\))?'
    all_sets = re.findall(set_pattern, score_str)

    num_sets = len(all_sets)
    is_grand_slam = tournament_name in grand_slam_names if tournament_name else False

    if is_grand_slam:
        if num_sets in [3, 4]:
            return 0  # Straight
        elif num_sets == 5:
            return 1  # Decider
    else:
        if num_sets == 2:
            return 0  # Straight
        elif num_sets == 3:
            return 1  # Decider

    return -1

# --- Appliquer classifier ---
if tournament_col:
    data['Straight_Decider'] = data.apply(
        lambda row: robust_classifier(row[score_col], row[tournament_col]), axis=1
    )
else:
    data['Straight_Decider'] = data[score_col].apply(robust_classifier)

# --- Debug : premiers 10 matchs ---
st.subheader("🔍 Analyse Détaillée (Premiers 10)")
debug_df = data.head(10).copy()
debug_df['Score_Clean'] = debug_df[score_col].astype(str)
debug_df['Sets_Count'] = debug_df[score_col].apply(
    lambda x: len(re.findall(r'\d+-\d+(?:\(\d+\))?', str(x)))
)
display_cols = [score_col]
if tournament_col:
    display_cols.append(tournament_col)
display_cols += ['Sets_Count', 'Straight_Decider']

# Supprimer doublons de colonnes avant affichage
df_display = debug_df[display_cols]
df_display = df_display.loc[:, ~df_display.columns.duplicated()]
st.dataframe(df_display, use_container_width=True)

# --- Stats globales ---
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

# --- Colonne à copier ---
st.subheader("📋 COPIER ICI")
st.write("**0 = Straight Sets | 1 = Decider Sets**")

copy_data = data['Straight_Decider'].astype(str)
st.code("\n".join(copy_data.values), language=None)

# --- Download ---
csv_data = data[[score_col, 'Straight_Decider']].to_csv(index=False)
st.download_button("💾 CSV Complet", csv_data, "tennis_results.csv")

st.success("✅ Analyse terminée.")
