import streamlit as st
import pandas as pd
from io import StringIO
import re

st.title("🎾 Tennis Straight/Decider Sets Classifier - CORRIGÉ")

st.write("Collez vos données. Straight = 0, Decider = 1.")

# Upload ou collage
uploaded_file = st.file_uploader("📁 Fichier CSV", type=['csv'])
data_text = st.text_area("📋 Coller données CSV", height=200)

if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)
elif data_text:
    try:
        data = pd.read_csv(StringIO(data_text))
    except:
        st.error("❌ Erreur CSV")
        st.stop()
else:
    st.stop()

# Colonne score
score_cols = [col for col in data.columns if any(word in str(col).lower() for word in ['score', 'resultat', 'result', 'résultat'])]
if score_cols:
    score_col = score_cols[0]
    st.success(f"✅ {score_col}")
else:
    st.error("❌ Colonne score manquante")
    st.stop()

# CORRECTION : Classifier avec l'ordre inversé
def classify_straight_decider(score_str):
    if pd.isna(score_str):
        return -1
    
    score_str = str(score_str).strip()
    score_str = re.sub(r'[^\d\-\s\(\)]', '', score_str)
    score_str = score_str.replace(' ', '')
    score_upper = score_str.upper()
    
    # Compter les sets
    set_pattern = r'(\d+-\d+(?:\([\d]+\))?)(?:\([\d]+\))?'
    sets = re.findall(set_pattern, score_str)
    
    if len(sets) < 2:
        return -1
    
    # Scores principaux
    set_scores = [re.search(r'(\d+-\d+)', s).group(1) for s in sets if re.search(r'(\d+-\d+)', s)]
    
    if len(set_scores) < 2:
        return -1
    
    num_sets = len(set_scores)
    
    # ✅ CORRECTION : Straight d'abord (2 sets = 0)
    if num_sets == 2:
        return 0
    
    # ✅ Decider ensuite (3 sets = 1)
    if num_sets == 3:
        return 1
    
    # Patterns explicites
    straight_patterns = ['2-0', '3-0']
    decider_patterns = ['2-1', '3-1', '3-2']
    
    if any(p in score_upper for p in straight_patterns):
        return 0
    elif any(p in score_upper for p in decider_patterns):
        return 1
    
    return -1

# Appliquer
data['Straight_Decider'] = data[score_col].apply(classify_straight_decider)

# Aperçu
st.subheader("🔍 10 Premiers Résultats")
sample = data.head(10).copy()
sample['Score'] = sample[score_col].astype(str)
st.dataframe(sample[['Score', 'Straight_Decider']], use_container_width=True)

# Stats
st.subheader("📊 Statistiques")
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

# Colonne à copier
st.subheader("📋 COPIER ICI (0 = Straight, 1 = Decider)")
copy_data = data[data['Straight_Decider'] != -1]['Straight_Decider'].astype(str)
if len(copy_data) > 0:
    st.code("\n".join(copy_data.values), language=None)
    st.success(f"✅ {len(copy_data)}/{total} classifiés")
else:
    st.warning("❌ Aucun match détecté")

# Download
csv_data = data[[score_col, 'Straight_Decider']].to_csv(index=False)
st.download_button("💾 CSV Complet", csv_data, "tennis_results.csv")

st.info("""
**Utilisation :**
1. Collez vos données CSV
2. Copiez la colonne CODE ci-dessus
3. Collez dans Excel
**0 = Straight Sets | 1 = Decider Sets**
""")
