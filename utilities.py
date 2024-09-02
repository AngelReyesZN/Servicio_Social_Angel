import pandas as pd
import unicodedata

def separate_hours(hours):
    """Transform string hh:mm-hh:mm to float."""
    if hours == '-':
        return None, None
    start, end = hours.split("-")
    start, end = start.lstrip("0").replace(":00", ""), end.lstrip("0").replace(":00", "")
    return float(start), float(end)

def remove_accents(input_str):
    """Remove accents and punctuation from a string."""
    if isinstance(input_str, str):
        return ''.join(c for c in unicodedata.normalize('NFKD', input_str) if not unicodedata.combining(c))
    return input_str

def read_siia(path):
    """Import and process SIIA Excel data."""
    columns_mapping = {
        'SEMESTRE': 'BLOQUE', 'MATERIA': 'CVEM', 'NOMBREMATE': 'MATERIA',
        'AREA': 'PE', 'MAESTRO': 'CVE PROFESOR', 'NOMBRE': 'PROFESOR'
    }
    
    # TODO: try catch format NOE
    
    siia = pd.read_excel(path, usecols="C:F,H,K,N,R:V,Z,AJ,AL,AN,AP,AR").rename(columns=columns_mapping)
    siia['CVE PROFESOR'] = siia['CVE PROFESOR'].astype(float)
    
    # Apply accent and punctuation removal
    siia['PROFESOR'] = siia['PROFESOR'].apply(remove_accents).str.replace(r'[.,]', '', regex=True)
    siia['MATERIA'] = siia['MATERIA'].apply(remove_accents).str.replace(r'[.,]', '', regex=True)
    
    # Replace special characters
    siia['PROFESOR'] = siia['PROFESOR'].str.replace(r'—', 'Ñ', regex=True)
    siia['MATERIA'] = siia['MATERIA'].str.replace("—", "Ñ", case=False, regex=True)
    
    # Adjust GRUPO column
    siia['GRUPO'] = siia['GRUPO'] % 100

    # Process days of the week
    dias = ['LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES']
    for d in dias:
        siia[[d[:2], d[:2]+'.1']] = siia[d].apply(separate_hours).apply(pd.Series)
    siia.drop(labels=dias, axis=1, inplace=True)
    
    # Process AULA data
    for i, d in enumerate(dias):
        sa_column = 'SA' if i == 0 else f'SA.{i}'
        siia[sa_column] = siia['AULA'].where(pd.notna(siia[d[:2]]))
    siia.drop(labels=['AULA'], axis=1, inplace=True)
    
    # Check and process different SA values
    dias_aula = ['LUNES', 'MARTES', 'MIERCO', 'JUEVES', 'VIERNE']
    for i, d in enumerate(dias_aula):
        sa_column = 'SA' if i == 0 else f'SA.{i}'
        aula_column = f'AULA{d}'
        siia[sa_column] = siia[aula_column].where(pd.notna(siia[aula_column]), siia[sa_column])
        siia.drop(labels=[aula_column], axis=1, inplace=True)
    
    # Convert data types and aggregate
    siia = siia.convert_dtypes()
    aggregated = siia.groupby(['GRUPO', 'BLOQUE', 'CVEM', 'PE', 'CVE PROFESOR'], as_index=False).agg(
        {col: 'max' for col in siia.columns if col not in ['GRUPO', 'BLOQUE', 'CVEM', 'PE', 'CVE PROFESOR']}
    )
    return aggregated

def read_ch(path):
    """Import and process CH Excel data."""
    # TODO: try catch format OBED
    ch = pd.read_excel(path, skiprows=4).drop(columns=['No'])
    return ch.convert_dtypes()