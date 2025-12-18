# ==============================
# Analyse complète centrale PV
# ==============================

# Étape 0 : Import des librairies
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ==============================
# Étape 1 : Lecture et nettoyage
# ==============================
df = pd.read_excel("Dataset centrale PV.xlsx")
df['Date'] = pd.to_datetime(df['Date'])

# Nettoyage des noms de colonnes (supprimer espaces invisibles)
df.columns = [c.strip() for c in df.columns]

# Définir l'index datetime
df.set_index('Date', inplace=True)

# Remplacer les irradiations négatives par 0
irradiation_cols = ['Irradiation (Horizontal) [W/m²]',
                    'Irradiation (Plan de module) [W/m²]',
                    'Irradiation (ALBEDO) [W/m²]']

for col in irradiation_cols:
    df[col] = df[col].apply(lambda x: max(x, 0))

print("Valeurs manquantes par colonne :")
print(df.isnull().sum())

# Interpolation temporelle
df.interpolate(method='time', inplace=True)

# ==============================
# Étape 2 : Statistiques globales
# ==============================
stats = df.describe()
print("\nStatistiques globales :")
print(stats)

hours_zero_power = (df['Puissance [kW]'] == 0).sum()
print(f"\nNombre d'heures avec puissance = 0 : {hours_zero_power}")




# ==============================
# Étape 3 : Calculs journaliers
# ==============================
daily = df.resample('D').agg({
    'Température module [°C]': ['mean', 'max'],
    'Puissance [kW]': 'sum',
    'Irradiation (Plan de module) [W/m²]': 'sum'
})

# Renommer les colonnes pour simplifier
daily.columns = ['Temp_module_moy', 'Temp_module_max', 'Energie_journaliere', 'Irradiation_journaliere']

# Calcul du RP
puissance_installee = 4641  # kWc
daily['RP'] = daily['Energie_journaliere'] / (puissance_installee * daily['Irradiation_journaliere'])

# Identifier l'heure de température max et puissance correspondante
def heure_temp_max(group):
    idx = group['Température module [°C]'].idxmax()
    return idx

heures_temp_max = df.groupby(df.index.date).apply(heure_temp_max)
daily['Heure_temp_max'] = heures_temp_max.values
daily['Puissance_temp_max'] = [df.loc[dt, 'Puissance [kW]'] for dt in heures_temp_max]

# ==============================
# Étape 4 : Affichage et export
# ==============================
print("\n--- Tableau journalier récapitulatif ---")
print(daily.head())

# Export Excel si besoin
daily.to_excel("Tableau_journalier_complet.xlsx", sheet_name="Journalier")
print("✅ Export terminé : 'Tableau_journalier_complet.xlsx'")

# ==============================
# Étape 5 : Graphiques journaliers
# ==============================
import matplotlib.dates as mdates

# Graphique RP
plt.figure(figsize=(12,5))
plt.plot(daily.index, daily['RP'], marker='o', linestyle='-')
plt.title("Évolution journalière du RP")
plt.xlabel("Jour")
plt.ylabel("RP")
plt.grid(True)
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Graphique résumé : RP, Température max et Énergie produite
fig, ax1 = plt.subplots(figsize=(14,6))

# RP
ax1.plot(daily.index, daily['RP'], color='blue', marker='o', label='RP')
ax1.set_xlabel("Jour")
ax1.set_ylabel("RP", color='blue')
ax1.tick_params(axis='y', labelcolor='blue')

# Température max
ax2 = ax1.twinx()
ax2.plot(daily.index, daily['Temp_module_max'], color='red', marker='x', label='Température max [°C]')
ax2.set_ylabel("Température max [°C]", color='red')
ax2.tick_params(axis='y', labelcolor='red')

# Énergie produite
ax3 = ax1.twinx()
ax3.spines["right"].set_position(("axes", 1.15))
ax3.plot(daily.index, daily['Energie_journaliere'], color='green', marker='s', label='Énergie produite [kWh]')
ax3.set_ylabel("Énergie produite [kWh]", color='green')
ax3.tick_params(axis='y', labelcolor='green')

plt.title("Résumé journalier : RP, Température max et Énergie produite")
fig.tight_layout()
plt.show()

# ==============================
# Étape 6 : Export Excel
# ==============================

# Tableau horaire : puissance mesurée
tableau_horaire = df[['Puissance [kW]']].copy()

# Tableau journalier complet
tableau_journalier_complet = daily[['Temp_module_moy', 
                                    'Temp_module_max', 
                                    'Heure_temp_max', 
                                    'Puissance_temp_max',
                                    'Irradiation_journaliere',
                                    'Energie_journaliere',
                                    'RP']]

# Export dans un fichier Excel avec deux feuilles
with pd.ExcelWriter("Analyse_Centrale_PV_Complet.xlsx") as writer:
    tableau_horaire.to_excel(writer, sheet_name="Horaire_Puissance")
    tableau_journalier_complet.to_excel(writer, sheet_name="Journalier_Resume")

print("✅ Export terminé : fichier 'Analyse_Centrale_PV_Complet.xlsx' créé !")



# ==============================
# Étape 7 : Graphique résumé journalier
# ==============================
fig, ax1 = plt.subplots(figsize=(14,6))

# RP
ax1.plot(tableau_journalier_complet.index, tableau_journalier_complet['RP'], color='blue', marker='o', label='RP')
ax1.set_xlabel("Jour")
ax1.set_ylabel("RP", color='blue')
ax1.tick_params(axis='y', labelcolor='blue')

# Température max
ax2 = ax1.twinx()
ax2.plot(tableau_journalier_complet.index, tableau_journalier_complet['Temp_module_max'], color='red', marker='x', label='Température max [°C]')
ax2.set_ylabel("Température max [°C]", color='red')
ax2.tick_params(axis='y', labelcolor='red')

# Énergie produite
ax3 = ax1.twinx()
ax3.spines["right"].set_position(("axes", 1.15))  # décaler le troisième axe
ax3.plot(tableau_journalier_complet.index, tableau_journalier_complet['Energie_journaliere'], color='green', marker='s', label='Énergie produite [kWh]')
ax3.set_ylabel("Énergie produite [kWh]", color='green')
ax3.tick_params(axis='y', labelcolor='green')

# Titre et mise en page
plt.title("Résumé journalier : RP, Température max et Énergie produite")
fig.tight_layout()
plt.show()

# ==============================
# Étape 8 : Détection des jours "anormaux"
# ==============================
rp_seuil = 0.6
irradiation_min = 50  # W/m²

# Jours avec RP faible
jours_rp_faible = tableau_journalier_complet[tableau_journalier_complet['RP'] < rp_seuil]

# Jours avec puissance nulle malgré irradiation
jours_puissance_zero = tableau_journalier_complet[
    (tableau_journalier_complet['Energie_journaliere'] == 0) &
    (tableau_journalier_complet['Irradiation_journaliere'] > irradiation_min)
]

# Affichage
print("\n--- Jours avec RP < {:.2f} ---".format(rp_seuil))
print(jours_rp_faible)

print("\n--- Jours avec puissance nulle malgré irradiation > {} W/m² ---".format(irradiation_min))
print(jours_puissance_zero)
# ==============================
# Étape 9 : Export des jours anormaux
# ==============================
with pd.ExcelWriter("Jours_Anormaux_PV.xlsx") as writer:
    jours_rp_faible.to_excel(writer, sheet_name="RP_faible")
    jours_puissance_zero.to_excel(writer, sheet_name="Puissance_zero")
    
print("\n✅ Export terminé : fichier 'Jours_Anormaux_PV.xlsx' créé !")

