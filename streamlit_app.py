
import streamlit as st
import pandas as pd
from io import StringIO
import re

st.set_page_config(page_title="Tennis Classifier - Robuste", layout="wide")

st.title("🎾 Tennis Classifier - Version Robuste (BO3 / BO5)")
st.write("Analyse automatique des scores pour Straight (0) vs Decider (1). Détection automatique des tournois du Grand Chelem (BO5).")

# --- Upload / Coller CSV ---
uploaded_file = st.file_uploader("📁 Fichier CSV", type=['csv'])
data_text = st.text_area("📋 Coller données CSV (CSV complet)", height=200)

if uploaded_file is None and not data_text:
    st.info("Téléverse un fichier CSV ou colle des données CSV dans la zone ci-dessus pour commencer.")
    st.stop()

try:
    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file)
    else:
        data = pd.read_csv(StringIO(data_text))
except Exception as e:
    st.error(f"Erreur lors de la lecture du CSV : {e}")
    st.stop()

# --- Déduplication sûre des noms de colonnes (évite l'erreur pyarrow) ---
def dedup_column_names(cols):
    seen = {}
    new_cols = []
    for c in cols:
        if c in seen:
            seen[c] += 1
            new_cols.append(f"{c}.{seen[c]}")
        else:
            seen[c] = 0
            new_cols.append(c)
    return new_cols

if data.columns.duplicated().any():
    data.columns = dedup_column_names(list(data.columns))

# --- Détection colonne score & tournoi ---
score_candidates = [col for col in data.columns if any(word in str(col).lower() for word in ['score', 'resultat', 'résultat', 'result'])]
if not score_candidates:
    st.error("❌ Colonne score non trouvée. Noms recherchés : score, resultat, résultat, result")
    st.stop()
score_col = score_candidates[0]
st.success(f"✅ Colonne score utilisée : {score_col}")

tournament_candidates = [col for col in data.columns if any(word in str(col).lower() for word in ['tournament', 'event', 'tournoi'])]
tournament_col = tournament_candidates[0] if tournament_candidates else None
if tournament_col:
    st.success(f"✅ Colonne tournoi détectée : {tournament_col}")
else:
    st.warning("⚠️ Colonne tournoi non détectée automatiquement. Le classifier utilisera la logique BO3 par défaut lorsque le tournoi est inconnu.")

# --- Liste Grand Slam (verif par sous-chaîne, insensible à la casse) ---
GRAND_SLAM_NAMES = ['Australian Open', 'Roland Garros', 'Wimbledon', 'US Open']

def is_grand_slam_name(tournament_name):
    if not tournament_name or not isinstance(tournament_name, str):
        return False
    tn = tournament_name.lower()
    return any(gs.lower() in tn for gs in GRAND_SLAM_NAMES)

# --- Classifier robuste ---
def robust_classifier(score_str, tournament_name=None):
    # valeurs manquantes
    if pd.isna(score_str):
        return -1

    s_orig = str(score_str).strip()

    # Normalisations :
    # - convertir dash unicode en '-'
    # - remplacer virgules par espaces (séparateurs)
    # - remplacer slash par '-'
    s = s_orig.replace('–', '-').replace('—', '-').replace('/', '-')
    s = s.replace(',', ' ')
    # Garder uniquement chiffres, tirets, parenthèses et espaces ; les autres caractères deviennent des espaces
    s = re.sub(r'[^0-9\-\(\)\s]', ' ', s)
    # Réduire les espaces multiples
    s = re.sub(r'\s+', ' ', s).strip()

    if not s:
        return -1

    # Pattern pour trouver chaque set, par ex. "7-6(5)" ou "6-4" (admet des espaces autour du '-')
    set_pattern = r'\d+\s*-\s*\d+(?:\s*\(\s*\d+\s*\))?'
    found = re.findall(set_pattern, s)

    if not found:
        # Pas de set détecté -> non classé
        return -1

    # Nettoyage des sets : normaliser "7 - 6 (5)" -> "7-6(5)" puis enlever l'info de tie-break pour compter les sets uniques
    clean_sets = []
    for item in found:
        # enlever les espaces inutiles
        it = re.sub(r'\s*-\s*', '-', item)
        it = re.sub(r'\(\s*', '(', it)
        it = re.sub(r'\s*\)', ')', it)
        clean_sets.append(it)

    # Pour compter les sets joués on retire la parenthèse de tie-break (ex: 7-6(5) -> 7-6)
    unique_sets = []
    for cs in clean_sets:
        base = re.sub(r'\(\d+\)', '', cs).strip()
        if base not in unique_sets:
            unique_sets.append(base)

    num_sets = len(unique_sets)

    # Détecter Grand Slam via le nom du tournoi si disponible
    is_gs = is_grand_slam_name(tournament_name) if tournament_name is not None else False

    # Règles explicites :
    if is_gs:
        # BO5 : 3 ou 4 sets -> Straight (0), 5 sets -> Decider (1)
        if num_sets in (3, 4):
            return 0
        elif num_sets == 5:
            return 1
        else:
            return -1
    else:
        # BO3 : 2 sets -> Straight (0), 3 sets -> Decider (1)
        if num_sets == 2:
            return 0
        elif num_sets == 3:
            return 1
        else:
            return -1

# --- Appliquer le classifier ---
if tournament_col:
    data['Straight_Decider'] = data.apply(lambda r: robust_classifier(r[score_col], r[tournament_col]), axis=1)
else:
    data['Straight_Decider'] = data[score_col].apply(lambda x: robust_classifier(x, None))

# --- Colonne Sets_Count pour debug (nombre de sets détectés) ---
def count_sets_detected(s):
    if pd.isna(s):
        return 0
    s = str(s)
    s = s.replace('–','-').replace('—','-').replace('/', '-').replace(',', ' ')
    s = re.sub(r'[^0-9\-\(\)\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    set_pattern = r'\d+\s*-\s*\d+(?:\s*\(\s*\d+\s*\))?'
    found = re.findall(set_pattern, s)
    # retirer doublons basés sur la base sans tie-break
    bases = []
    for it in found:
        it = re.sub(r'\s*-\s*', '-', it)
        base = re.sub(r'\(\d+\)', '', it).strip()
        if base not in bases:
            bases.append(base)
    return len(bases)

# --- Affichage Debug (premiers 10) ---
st.subheader("🔍 Analyse Détaillée (Premiers 10)")
debug_df = data.head(10).copy()
debug_df['Score_Original'] = debug_df[score_col].astype(str)
debug_df['Sets_Count'] = debug_df[score_col].apply(count_sets_detected)

display_cols = [score_col]
if tournament_col:
    display_cols.append(tournament_col)
display_cols += ['Sets_Count', 'Straight_Decider']

# enlever les colonnes qui pourraient ne pas exister après renaming
display_cols = [c for c in display_cols if c in debug_df.columns]
df_display = debug_df[display_cols]
df_display = df_display.loc[:, ~df_display.columns.duplicated()]
st.dataframe(df_display, use_container_width=True)

# --- Stats ---
st.subheader("📊 Résultats")
col1, col2, col3 = st.columns(3)
total = len(data)
straight = int((data['Straight_Decider'] == 0).sum())
decider = int((data['Straight_Decider'] == 1).sum())

with col1:
    st.metric("Total", total)
with col2:
   st.metric("Straight (0)", straight, f"{straight/total*100:.1f}%" if total else "0%")
with col3:
 st.metric("Decider (1)", decider, f"{decider/total*100:.1f}%" if total else "0%")

# --- Colonne à copier ---
st.subheader("📋 COPIER ICI")
st.write("**0 = Straight Sets | 1 = Decider Sets | -1 = Non classé**")
copy_data = data['Straight_Decider'].astype(str)
st.code("\n".join(copy_data.values), language=None)

# --- Téléchargement ---
download_cols = [c for c in [score_col, tournament_col, 'Straight_Decider'] if c is not None and c in data.columns]
csv_data = data[download_cols].to_csv(index=False)
st.download_button("💾 Télécharger CSV", csv_data, "tennis_results_classified.csv", mime="text/csv")

st.success("✅ Analyse terminée.")

# --- Outil de test rapide ---
with st.expander("🧪 Tests rapides (exemples et debug)"):
    example_scores = [
        ("Wimbledon", "7-6(5) 6-7(6) 6-4"),
        ("Wimbledon", "6-4 6-3 6-2"),
        ("US Open", "6-3 4-6 7-5 3-6 6-4"),
        ("Roland Garros", "7-6(9) 6-7(7) 6-3"),
        ("Unknown", "7-6(5) 6-7(6) 6-4"),
        (None, "6-4 6-3")
    ]
    rows = []
    for tn, sc in example_scores:
        rows.append({"Tournament": tn or "None", "Score": sc, "Detected": robust_classifier(sc, tn)})
    st.table(pd.DataFrame(rows))
    st.info("Vérifie ici que pour les tournois du Grand Chelem (ex: Wimbledon) 3 ou 4 sets donnent 0, et 5 sets donnent 1. Si tu as un exemple qui pose problème, colle-le dans la zone CSV en haut pour qu'on l'analyse dans ton dataset réel.")
