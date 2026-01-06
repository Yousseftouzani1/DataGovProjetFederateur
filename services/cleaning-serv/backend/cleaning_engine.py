import pandas as pd


# -------------------------------
# Missing rate (% of missing cells)
# -------------------------------
def missing_rate(df: pd.DataFrame) -> float:
    return round(df.isnull().mean().mean() * 100, 2)


# -------------------------------
# Remove duplicate rows
# -------------------------------
def remove_duplicates(df: pd.DataFrame):
    before = len(df)
    df_clean = df.drop_duplicates()
    removed = before - len(df_clean)
    return df_clean, removed


# -------------------------------
# Handle missing values
# -------------------------------
def handle_missing_values(df: pd.DataFrame, strategy: str) -> pd.DataFrame:
    if strategy == "drop":
        return df.dropna()

    if strategy not in ["mean", "median", "mode"]:
        strategy = "mean"  # safe default

    df_clean = df.copy()

    for col in df_clean.columns:
        if pd.api.types.is_numeric_dtype(df_clean[col]):
            if strategy == "mean":
                df_clean[col] = df_clean[col].fillna(df_clean[col].mean())
            elif strategy == "median":
                df_clean[col] = df_clean[col].fillna(df_clean[col].median())
        else:
            mode = df_clean[col].mode()
            if not mode.empty:
                df_clean[col] = df_clean[col].fillna(mode[0])

    return df_clean


# -------------------------------
# Remove outliers using IQR
# -------------------------------




# Suppression des valeurs aberrantes (outliers) par la méthode
# de l’Intervalle Interquartile (IQR – Interquartile Range)
#
# La méthode IQR est une technique statistique robuste utilisée
# pour détecter et supprimer les valeurs aberrantes dans des
# données numériques.

# Principe de l’algorithme :
# 1. Pour chaque colonne numérique, on calcule :
#    - Q1 : le premier quartile (25 % des données)
#    - Q3 : le troisième quartile (75 % des données)
# 2. On calcule ensuite l’intervalle interquartile :
#       IQR = Q3 - Q1
# 3. On définit les bornes acceptables :
#       borne_inférieure = Q1 - 1.5 × IQR
#       borne_supérieure = Q3 + 1.5 × IQR
# 4. Toute valeur située en dehors de cet intervalle est
#    considérée comme une valeur aberrante et est supprimée.





def remove_outliers_iqr(df: pd.DataFrame):
    removed = 0
    df_clean = df.copy()

    for col in df_clean.select_dtypes(include="number").columns:
        q1 = df_clean[col].quantile(0.25)
        q3 = df_clean[col].quantile(0.75)
        iqr = q3 - q1

        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        before = len(df_clean)
        df_clean = df_clean[(df_clean[col] >= lower) & (df_clean[col] <= upper)]
        removed += before - len(df_clean)

    return df_clean, removed






# -------------------------------
# MAIN PIPELINE FUNCTION
# -------------------------------
def clean_dataframe(df: pd.DataFrame, config: dict):
    """
    Applique un pipeline de nettoyage de données configurable
    et retourne le DataFrame nettoyé ainsi que des métriques
    de traçabilité.
    """
    metrics = {}

    # Métriques initiales
    metrics["rows_before"] = len(df)
    metrics["missing_rate_before"] = missing_rate(df)

    # Step 1: suppression des doublons
    if config.get("remove_duplicates", True):
        df, dup_removed = remove_duplicates(df)
        metrics["duplicates_removed"] = dup_removed
    else:
        metrics["duplicates_removed"] = 0

    # Step 2: gestion des valeurs manquantes
    strategy = config.get("handle_missing", "mean")
    df = handle_missing_values(df, strategy)

    # Step 3: suppression des valeurs aberrantes
    if config.get("remove_outliers", True):
        df, out_removed = remove_outliers_iqr(df)
        metrics["outliers_removed"] = out_removed
    else:
        metrics["outliers_removed"] = 0

    # Métriques finales
    metrics["rows_after"] = len(df)
    metrics["missing_rate_after"] = missing_rate(df)

    return df.reset_index(drop=True), metrics