import streamlit as st
import pandas as pd
from io import StringIO
import re

st.title("🎾 Tennis Straight/Decider Sets Classifier")

st.write("Collez vos données de matchs ci-dessous. Gère les formats complexes avec tie-breaks.")

# Upload ou collage de données
uploaded_file = st.file_uploader("📁 Choisir un fichier CSV", type=['csv'])
data_text = st.text_area("📋 Ou coller directement vos données CSV", height=200)

if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)
elif data_text:
    try:
        data = pd.read_csv(StringIO(data_text))
    except Exception as e:
        st.error(f"❌ Erreur CSV : {e}")
        st.stop()
else:
    st.stop()

# Trouver la colonne score
score_cols = [col for col in data.columns if any(word in str(col).lower() for word in ['score', 'resultat', 'result', 'résultat', 'score'])]
if score_cols:
    score_col = score_cols[0]
    st.success(f"✅ Colonne détectée : {score_col}")
else:
    st.error("❌ Pas de colonne 'score' ou 'résultat' trouvée.")
    st.stop()

# Classifier amélioré
def classify_straight_decider(score_str):
    if pd.isna(score_str):
        return -1
    
    score_str = str(score_str).strip()
    score_str = re.sub(r'[^\d\-\s\(\)]', '', score_str)  # Nettoyer
    score_str = score_str.replace(' ', '')  # Enlever espaces
    score_upper = score_str.upper()
    
    # Compter les sets
    set_pattern = r'(\d+-\d+(?:\([\d]+\))?)(?:\([\d]+\))?'
    sets = re.findall(set_pattern, score_str)
    
    if len(sets) < 2:
        return -1
    
    # Scores principaux (sans tie-breaks)
    set_scores = [re.search(r'(\d+-\d+)', s).group(1) for s in sets if re.search(r'(\d+-\d+)', s)]
    
    if len(set_scores) < 2:
        return -1
    
    num_sets = len(set_scores)
    
    # Règles principales
    if num_sets == 2:
        return 0  # Straight sets
    
    if num_sets == 3:
        return 1  # Decider sets
    
    # Patterns explicites
    straight_patterns = ['2-0', '3-0']
    decider_patterns = ['2-1', '3-1', '3-2']
    
    if any(p in score_upper for p in straight_patterns):
        return 0
    elif any(p in score_upper for p in decider_patterns):
        return 1
    
    return -1

# Appliquer la classification
data['Straight_Decider'] = data[score_col].apply(classify_straight_decider)

# Aperçu
st.subheader("🔍 Aperçu (10 premiers)")
sample = data.head(10).copy()
sample['Score'] = sample[score_col].astype(str)
st.dataframe(sample[['Score', 'Straight_Decider']], use_container_width=True)

# Statistiques
st.subheader("📊 Statistiques")
col1, col2, col3, col4 = st.columns(4)
total = len(data)
straight = len(data[data['Straight_Decider'] == 0])
decider = len(data[data['Straight_Decider'] == 1])
unknown = len(data[data['Straight_Decider'] == -1])

with col1:
    st.metric("Total", total)
with col2:
    st.metric("Straight (0)", straight, f"{straight/total*100:.1f}%" if total else "0%")
with col3:
    st.metric("Decider (1)", decider, f"{decider/total*100:.1f}%" if total else "0%")
with col4:
    st.metric("Inconnus (-1)", unknown, f"{unknown/total*100:.1f}%" if total else "0%")

# Colonne à copier
st.subheader("📋 Colonne à Copier dans Excel")
st.write("**0 = Straight Sets | 1 = Decider Sets**")

copy_data = data[data['Straight_Decider'] != -1]['Straight_Decider'].astype(str)
if len(copy_data) > 0:
    st.code("\n".join(copy_data.values), language=None)
    st.success(f"✅ {len(copy_data)}/{total} matchs classifiés")
else:
    st.warning("❌ Aucun match classifiable")

# Download
csv_data = data[[score_col, 'Straight_Decider']].to_csv(index=False)
st.download_button("💾 Télécharger CSV", csv_data, "tennis_results.csv")

st.info("""
**Utilisation :**
1. Collez vos données CSV (avec colonne Score)
2. Copiez la colonne affichée ci-dessus
3. Collez dans votre Excel
4. **0 = Victoire directe** | **1 = Match à 3 sets**
""")
