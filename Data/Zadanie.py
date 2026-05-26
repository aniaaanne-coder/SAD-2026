import pandas as pd
import numpy as np

# ============================================================
# WCZYTANIE DANYCH
# ============================================================
df_voting = pd.read_excel(r'C:\Users\aniaa\PycharmProjects\SAD-2026\Data\eurovision.xlsx', sheet_name='Voting Final')
df_meta   = pd.read_excel(r'C:\Users\aniaa\PycharmProjects\SAD-2026\Data\eurovision.xlsx', sheet_name='eurovision_meta')

print("=" * 60)
print("KROK 1: INSPEKCJA DANYCH")
print("=" * 60)
print(f"Voting Final:    {df_voting.shape[0]} wierszy, {df_voting.shape[1]} kolumny")
print(f"eurovision_meta: {df_meta.shape[0]} wierszy, {df_meta.shape[1]} kolumny")
print(f"\nLata w Voting Final: {sorted(df_voting['Year'].unique())}")
print(f"Lata w meta:         {sorted(df_meta['Year'].unique())}")


# ============================================================
# KROK 2: BRAKUJĄCE WARTOŚCI
# ============================================================
print("\n" + "=" * 60)
print("KROK 2: BRAKUJĄCE WARTOŚCI")
print("=" * 60)

print("\nVoting Final — NaN per kolumna:")
print(df_voting.isna().sum())

print("\neurovision_meta — NaN w kluczowych kolumnach:")
kluczowe = ['Year', 'Country', 'Region', 'Home.Away.Country', 'Home.Away.Region']
print(df_meta[kluczowe].isna().sum())

# brak NaN w kluczowych kolumnach — brak akcji wymaganej


# ============================================================
# KROK 3: WALIDACJA WARTOŚCI SCORE (brudne dane)
# ============================================================
print("\n" + "=" * 60)
print("KROK 3: WALIDACJA SCORE")
print("=" * 60)

dozwolone = {0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12}
print(f"Unikalne wartości Score: {sorted(df_voting['Score'].unique())}")
nieprawidlowe = df_voting[~df_voting['Score'].isin(dozwolone)]
print(f"Nieprawidłowe wartości Score: {len(nieprawidlowe)}")
# wszystkie wartości poprawne — brak akcji wymaganej


# ============================================================
# KROK 4: DUPLIKATY
# ============================================================
print("\n" + "=" * 60)
print("KROK 4: DUPLIKATY")
print("=" * 60)

dup_voting = df_voting.duplicated(subset=['Year', 'Country', 'Giver']).sum()
print(f"Voting Final — duplikaty (Year+Country+Giver): {dup_voting}")

# Meta zawiera te same kraje w finale i półfinale — to prawidłowe
# Filtrujemy meta tylko do finałów (Is.Final == 1)
df_meta_final = df_meta[df_meta['Is.Final'] == 1].copy()
dup_meta_final = df_meta_final.duplicated(subset=['Year', 'Country']).sum()
print(f"eurovision_meta (tylko finały) — duplikaty: {dup_meta_final}")
print(f"Rozmiar meta po filtrze finałów: {df_meta_final.shape[0]} wierszy")


# ============================================================
# KROK 5: HARMONIZACJA NAZW KRAJÓW (brudne dane)
# ============================================================
print("\n" + "=" * 60)
print("KROK 5: HARMONIZACJA NAZW KRAJÓW")
print("=" * 60)

countries_voting = set(df_voting['Country'].unique()) | set(df_voting['Giver'].unique())
countries_meta   = set(df_meta_final['Country'].unique())

only_voting = sorted(countries_voting - countries_meta)
only_meta   = sorted(countries_meta - countries_voting)
print(f"Tylko w Voting Final: {only_voting}")
print(f"Tylko w meta:         {only_meta}")

# Słownik korekt — ujednolicamy do nazw z meta
mapping = {
    'Bosnia-Herzegovina': 'Bosnia and Herzegovina'
}

df_voting['Country'] = df_voting['Country'].replace(mapping)
df_voting['Giver']   = df_voting['Giver'].replace(mapping)

# Weryfikacja po korekcie
countries_voting_po = set(df_voting['Country'].unique()) | set(df_voting['Giver'].unique())
pozostale = sorted(countries_voting_po - countries_meta)
print(f"\nPo korekcie — kraje bez dopasowania w meta: {pozostale}")


# ============================================================
# KROK 6: TIDY DATA — weryfikacja formatu
# ============================================================
print("\n" + "=" * 60)
print("KROK 6: TIDY DATA")
print("=" * 60)
print("Voting Final — każdy wiersz to jedna obserwacja Year | Giver | Country | Score")
print(f"  Unikalnych kombinacji Year+Giver+Country: "
      f"{df_voting[['Year','Country','Giver']].drop_duplicates().shape[0]}")
print(f"  Łączna liczba wierszy:                   {df_voting.shape[0]}")
print("Format długi (long) — spełnia zasady tidy data ✓")


# ============================================================
# KROK 7: MERGE — łączenie zbiorów
# ============================================================
print("\n" + "=" * 60)
print("KROK 7: MERGE")
print("=" * 60)

meta_cols = ['Year', 'Country', 'Region', 'Home.Away.Country', 'Home.Away.Region']

# Merge 1: dołącz info o kraju OTRZYMUJĄCYM punkty
df = df_voting.merge(
    df_meta_final[meta_cols],
    on=['Year', 'Country'],
    how='left'
)
print(f"Po Merge 1 (Country): {df.shape[0]} wierszy")
print(f"  NaN w Region po merge: {df['Region'].isna().sum()}")

# Zmiana nazw przed Merge 2
df = df.rename(columns={
    'Region':             'Region_Country',
    'Home.Away.Country':  'Is.Host',
    'Home.Away.Region':   'Host.Same.Region'
})

# Merge 2: dołącz Region dla GIVERA
df = df.merge(
    df_meta_final[['Year', 'Country', 'Region']].rename(
        columns={'Country': 'Giver', 'Region': 'Region_Giver'}
    ),
    on=['Year', 'Giver'],
    how='left'
)
print(f"Po Merge 2 (Giver):  {df.shape[0]} wierszy")
print(f"  NaN w Region_Giver po merge: {df['Region_Giver'].isna().sum()}")

# Kraje bez dopasowania (Giverzy których nie ma w meta finałów)
brak_giver = df[df['Region_Giver'].isna()]['Giver'].unique()
print(f"  Giverzy bez regionu: {sorted(brak_giver)}")


# ============================================================
# KROK 8: NOWE ZMIENNE
# ============================================================
print("\n" + "=" * 60)
print("KROK 8: NOWE ZMIENNE")
print("=" * 60)

# Same.Region: czy Giver i Country z tego samego regionu
df['Same.Region'] = (df['Region_Country'] == df['Region_Giver']).astype('Int64')
df.loc[df['Region_Country'].isna() | df['Region_Giver'].isna(), 'Same.Region'] = pd.NA

# Is.Host.Binary: czytelna flaga binarna gospodarza
df['Is.Host.Binary'] = (df['Is.Host'] == 'Home').astype('Int64')
df.loc[df['Is.Host'].isna(), 'Is.Host.Binary'] = pd.NA

# Top.Vote: czy dano maksymalne 12 punktów
df['Top.Vote'] = (df['Score'] == 12).astype(int)

print(f"Same.Region — rozkład:\n{df['Same.Region'].value_counts(dropna=False)}")
print(f"\nIs.Host.Binary — rozkład:\n{df['Is.Host.Binary'].value_counts(dropna=False)}")
print(f"\nTop.Vote — liczba głosów 12 pkt: {df['Top.Vote'].sum()}")


# ============================================================
# KROK 9: FILTROWANIE
# ============================================================
print("\n" + "=" * 60)
print("KROK 9: FILTROWANIE")
print("=" * 60)

df_all    = df.copy()                      # pełny dataset (z zerami)
df_nonzero = df[df['Score'] > 0].copy()   # tylko niezerowe głosy
df_top    = df[df['Score'] == 12].copy()  # tylko maksymalne głosy

print(f"Pełny dataset (z zerami):      {df_all.shape[0]} wierszy")
print(f"Tylko Score > 0:               {df_nonzero.shape[0]} wierszy")
print(f"Tylko Score == 12 (faworyt):   {df_top.shape[0]} wierszy")


# ============================================================
# KROK 10: TRANSFORMACJA SCORE
# ============================================================
print("\n" + "=" * 60)
print("KROK 10: TRANSFORMACJA SCORE")
print("=" * 60)

print("Rozkład Score (niezerowe):")
print(df_nonzero['Score'].describe().round(2))
print(f"\nSkośność Score:       {df_nonzero['Score'].skew():.3f}")

# Transformacja log+1 (Score może być 0, więc log1p)
df_all['Score_log1p'] = np.log1p(df_all['Score'])
print(f"Skośność Score_log1p: {df_all['Score_log1p'].skew():.3f}")

# Z-score normalizacja w ramach roku (porównania między latami)
df_all['Score_zscore'] = df_all.groupby('Year')['Score'].transform(
    lambda x: (x - x.mean()) / x.std()
)
print(f"Score_zscore — przykład (mean≈0, std≈1 per rok): "
      f"mean={df_all['Score_zscore'].mean():.3f}, std={df_all['Score_zscore'].std():.3f}")


# ============================================================
# KROK 11: AGREGACJA — tabela par krajów
# ============================================================
print("\n" + "=" * 60)
print("KROK 11: AGREGACJA PER PARA KRAJÓW")
print("=" * 60)

agg = (df_all
    .groupby(['Giver', 'Country', 'Region_Giver', 'Region_Country',
              'Same.Region'], dropna=False)
    .agg(
        Suma_punktow   = ('Score', 'sum'),
        Srednia_punktow= ('Score', 'mean'),
        Liczba_lat     = ('Year', 'nunique'),
        Ile_razy_12    = ('Top.Vote', 'sum')
    )
    .reset_index()
    .sort_values('Suma_punktow', ascending=False)
)

print(f"Liczba unikalnych par Giver→Country: {len(agg)}")
print("\nTop 10 par z najwyższą sumą punktów:")
print(agg.head(10)[['Giver','Country','Region_Giver','Region_Country',
                     'Same.Region','Suma_punktow','Srednia_punktow',
                     'Liczba_lat','Ile_razy_12']].to_string(index=False))


# ============================================================
# KROK 12: WERYFIKACJA KOŃCOWA
# ============================================================
print("\n" + "=" * 60)
print("KROK 12: WERYFIKACJA KOŃCOWA")
print("=" * 60)

print("NaN w finalnym datasecie (df_all):")
print(df_all[['Score','Region_Country','Region_Giver',
              'Same.Region','Is.Host.Binary','Top.Vote',
              'Score_log1p','Score_zscore']].isna().sum())

print("\nPrzykład efektu sąsiedztwa — średni Score wg Same.Region:")
print(df_all.groupby('Same.Region')['Score'].mean().round(3))

print("\nPrzykład efektu gospodarza — średni Score wg Is.Host.Binary:")
print(df_all.groupby('Is.Host.Binary')['Score'].mean().round(3))

print("\nCztery grupy (Same.Region × Is.Host.Binary) — średni Score:")
print(df_all.groupby(['Same.Region', 'Is.Host.Binary'])['Score']
      .mean().round(3).to_string())

print("\nPreprocessing zakończony.")
print(f"Finalny dataset: {df_all.shape[0]} wierszy, {df_all.shape[1]} kolumn")
print(f"Kolumny: {list(df_all.columns)}")