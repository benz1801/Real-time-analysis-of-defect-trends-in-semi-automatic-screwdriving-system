# Script python per stimare i limiti di controllo sulle durate delle avvitature dei prodotti

import MAIN_COND_STD    
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore", message=".* will be removed.*", category = FutureWarning)
warnings.simplefilter(action='ignore', category=RuntimeWarning)

MAIN_COND_STD
df = pd.read_csv('Pset_DF_cond.csv',low_memory=False)
df['StartTime'] = pd.to_datetime(df['StartTime'],format='%Y-%m-%d %H:%M:%S')

# Drop dei valori anomali, duplicati e dei semilavorati
df = df[~df.Global_ID.str.contains('Y')]
df = df[df.Errors>=0]
df = df[df.Batch != 0]
df = df[df.meanDuration>=0]
df = df[(df.group_size >=2) & (df.group_size<=25)]
duplicated = df.duplicated(subset = df.columns.difference(['count_Operation','File_path']))

df = df[~duplicated]

# Dizionario che esprime il numero di osservazioni presenti in ogni Global_ID
units = df.shape[0]
Global = {}
for glob in df.Global_ID.unique():
    perc = len(df[df.Global_ID == glob])/units*100
    Global[glob] = (len(df[df.Global_ID == glob]), perc)
    
global_dict = dict(sorted(Global.items(), key = lambda x: x[1], reverse = True))

print('Global ID presenti nel dataset con frequenze assolute e relative delle osservazioni:')
print(global_dict)

# Numero di global e di seriali
print(f'Numero di Global: {len(df.Global_ID.unique())} e di Seriali: {len(df.SerialNumber.unique())}')
print('__________________________________________________________\n')

# Descrittive
print('Alcune descrittive: \n')
print(df.describe())
print('__________________________________________________________\n')

# Creazione della trasformata logaritmica della colonna Durations
df['logDuration'] = np.log(df['Duration'])
df = df[~np.isinf(df.logDuration)]

# Creazione della trasformata logaritmica della colonna meanDuration
df['logmeanDuration'] = np.log(df['meanDuration'])
df = df[~np.isinf(df.logmeanDuration)]
df = df.reset_index(drop=True)

# STIMA DEI LIMITI DI CONTROLLO PER X-BAR CHART
# Raggruppamento per Global e PSet
grouped_df = df.groupby(['Global_ID','Pset_ID'])

# Computo media e std. deviation per ogni sottogruppo
df['MeanDuration'] = grouped_df.logmeanDuration.transform('mean')
df['Std_devDuration'] = grouped_df.logmeanDuration.transform('std')

# Computo lower/upper limits per ogni sottogruppo
df['Lower_Limit'] = df.MeanDuration - 3*df.Std_devDuration
df['Upper_Limit'] = df.MeanDuration + 3*df.Std_devDuration

# Computo osservazioni in deriva
df['Derive'] = (df['logmeanDuration'] > df['Upper_Limit']) | (df['logmeanDuration'] < df['Lower_Limit'])

df_derive = df[df.Derive==True][['Global_ID','SerialNumber','Pset_ID','Step_Instruction','File_path']]
#df_derive.to_csv('Observations_Derive.csv', index = False)

# STIMA DEI LIMITI DI CONTROLLO PER R CHART
df['Range'] = grouped_df.logmeanDuration.transform(np.ptp)

assignD4 = {2: 3.267, 3: 2.574, 4: 2.238, 5: 2.114, 6: 2.004, 7: 1.924, 8: 1.864, 9: 1.816, 10: 1.777, 11: 1.744, 12: 1.717, 13: 1.693, 14: 1.672, 15: 1.653,
    16: 1.637, 17: 1.622, 18: 1.608, 19: 1.597, 20: 1.585, 21: 1.575, 22: 1.566, 23: 1.557, 24: 1.548, 25: 1.541
    }

assignD3 = { 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0.076, 8: 0.136, 9: 0.184, 10: 0.223, 11: 0.256, 12: 0.283, 13: 0.307, 14: 0.328, 15: 0.347, 16: 0.363, 17: 0.378,
    18: 0.391, 19: 0.403, 20: 0.415, 21: 0.425, 22: 0.434, 23: 0.443, 24: 0.451, 25: 0.459
    }
# Computo lower/upper limits per ogni sottogruppo
D3 = []
D4 = []
for i in range(len(df)):
    size = df.loc[i,'group_size']
    D3.append(assignD3.get(size,0))

for i in range(len(df)):
    size = df.loc[i,'group_size']
    D4.append(assignD4.get(size,0))

df['D3'] = D3
df['D4'] = D4

df['Lower_Limit_RChart'] = df.Range*df.D3
df['Upper_Limit_RChart'] = df.Range*df.D4

# Numero di derive per ogni seriale
serial_dict_derive = {}
for seriale in df_derive.SerialNumber:
    if seriale in serial_dict_derive:
        serial_dict_derive[seriale]+=1
    else:
        serial_dict_derive[seriale] = 1

print('Seriali con rispettivo numero di derive secondo l\'algoritmo di stima dei limiti: \n')
print(sorted(serial_dict_derive.items(), key = lambda x: x[1], reverse = True))

# Esportazione dataset per Data Visualisation in PBI
df[['SerialNumber','Global_ID','Tool_ID','Pset_ID','Fase','Operatore','Batch','Outcome','Step_Instruction','group_size','StartTime',
    'Errors','Error_percentage','Duration','meanDuration','logDuration','logmeanDuration','MeanDuration','Std_devDuration','Lower_Limit','Upper_Limit',
    'Derive','Range','Lower_Limit_RChart','Upper_Limit_RChart']].to_csv('Dataframe_PBI.csv', index = False)
print(input("Premere INVIO per uscire..."))