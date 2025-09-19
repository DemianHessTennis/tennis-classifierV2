# Réinstaller pour être sûr
!pip install streamlit pandas

# Code amélioré
%%writefile tennis_classifier.py
import streamlit as st
import pandas as pd
from io import StringIO
import re

st.title("🎾 Tennis Straight/Decider Sets Classifier - Version Améliorée")

st.write("Collez vos données de matchs ci-dessous. Le classificateur gère maintenant les formats complexes.")

# Upload ou collage de données
uploaded_file = st.file_uploader("Choisir un fichier CSV", type=['csv'])
data_text = st.text_area("Ou coller directement vos données CSV", height=200)

if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)
elif data_text:
    try:
        data = pd.read_csv(StringIO(data_text))
    except:
        st.error("Erreur de format CSV. Vérifiez vos données.")
        st.stop()
else:
    st.stop()

# Trouver la colonne score
score_cols = [col for col in data.columns if any(word in col.lower() for word in ['score', 'resultat', 'result', 'résultat', 'score'])]
if score_cols:
    score_col = score_cols[0]
    st.success(f"Colonne score détectée : {score_col}")
else:
    st.error("Colonne 'score' ou 'résultat' non trouvée.")
    st.stop()

# Classifier amélioré
def classify_straight_decider_advanced(score_str):
    if pd.isna(score_str):
        return -1
    
    # Nettoyer et standardiser le score
    score_str = str(score_str).strip()
    score_str = re.sub(r'[^\d\-\s\(\)]', '', score_str)  # Garder seulement chiffres, -, espaces, parenthèses
    score_str = score_str.replace(' ', '')  # Enlever les espaces
    
    # Compter le nombre de sets (séquences de chiffres séparés par -)
    set_pattern = r'(\d+-\d+(?:\(\d+\))?)(?:\(\d+\))?'
    sets = re.findall(set_pattern, score_str)
    
    if len(sets) < 2:
        return -1
    
    # Extraire les scores de sets (ignorer les tie-breaks pour compter les sets)
    set_scores = []
    for s in sets:
        # Extraire le score principal (avant parenthèses)
        main_score = re.search(r'(\d+-\d+)', s)
        if main_score:
            set_scores.append(main_score.group(1))
    
    if len(set_scores) < 2:
        return -1
    
    # Détecter le nombre de sets joués
    num_sets = len(set_scores)
    
    # Détecter les patterns de scores finaux
    score_upper = score_str.upper()
    
    # Straight sets : 2-0 ou 3-0
    if num_sets == 2 and ('2-0' in score_upper or '3-0' in score_upper):
        return 0
    
    # Decider sets : 2-1, 3-1, 3-2
    if num_sets == 3 and any(pattern in score_upper for pattern in ['2-1', '3-1', '3-2']):
        return 1
    
    # Règle heuristique : si 2 sets joués = straight, si 3 sets = decider
    if num_sets == 2:
        return 0
    elif num_sets == 3:
        return 1
    else:
        return -1

# Appliquer la classification
data['Straight_Decider'] = data[score_col].apply(classify_straight_decider_advanced)

# Debug : afficher quelques exemples
st.subheader("Exemples de Classification")
sample_data = data.head(10)[[score_col, 'Straight_Decider']]
st.dataframe(sample_data, use_container_width=True)

# Statistiques
st.subheader("Statistiques")
col1, col2, col3, col4 = st.columns(4)
total = len(data)
straight = len(data[data['Straight_Decider'] == 0])
decider = len(data[data['Straight_Decider'] == 1])
unknown = len(data[data['Straight_Decider'] == -1])

with col1:
    st.metric("Total Matchs", total)
with col2:
    percent_straight = (straight/total*100) if total > 0 else 0
    st.metric("Straight Sets", straight, f"{percent_straight:.1f}%")
with col3:
    percent_decider = (decider/total*100) if total > 0 else 0
    st.metric("Decider Sets", decider, f"{percent_decider:.1f}%")
with col4:
    percent_unknown = (unknown/total*100) if total > 0 else 0
    st.metric("Inconnus", unknown, f"{percent_unknown:.1f}%")

# Colonne à copier
st.subheader("Colonne à Copier-Coller dans Excel")
st.write("Copiez cette colonne (0 = Straight, 1 = Decider) :")

# Filtrer les inconnus
copy_data = data[data['Straight_Decider'] != -1]['Straight_Decider'].astype(str)
if len(copy_data) > 0:
    st.text_area("Colonne à copier :", "\n".join(copy_data), height=200)
    st.success(f"✅ {len(copy_data)} matchs classifiables sur {total}")
else:
    st.warning("Aucun match classifiable trouvé.")

# Téléchargement
display_cols = [score_col, 'Straight_Decider']
csv_data = data[display_cols].to_csv(index=False)
st.download_button("📥 Télécharger CSV complet", csv_data, "tennis_results.csv", "text/csv")
