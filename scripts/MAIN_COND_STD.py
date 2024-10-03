import os
from DF_BUILD import DF_BUILDING
from tkinter import filedialog

path = os.path.abspath(filedialog.askdirectory())
df = DF_BUILDING(path)

counter = 1  # Inizializza il contatore a 1

# Crea una lista per la nuova colonna
group_counter = [counter]

# Itera sulle righe del dataframe (a partire dalla seconda riga)
for i in range(1, len(df)):
    current_batch = df.loc[i, 'Batch']  # Ottieni il valore di Batch della riga corrente
    current_count_try = df.loc[i, 'count_Try']  # Ottieni il valore di count_Try della riga corrente
    prev_batch = df.loc[i-1, 'Batch']  # Ottieni il valore di Batch della riga precedente
    prev_count_try = df.loc[i-1, 'count_Try']  # Ottieni il valore di count_Try della riga precedente
    esito = df.loc[i,'Esito_finale']
    prev_esito = df.loc[i-1,'Esito_finale']
    prev_start = df.loc[i-1, 'StartTime']
    current_start = df.loc[i, 'StartTime']
    prev_serial = df.loc[i-1,'SerialNumber']
    current_serial = df.loc[i,'SerialNumber']

    time_difference = (current_start-prev_start).total_seconds()
    if (prev_count_try == prev_batch and prev_esito==1) or (prev_count_try != current_count_try and (current_count_try == 1 or current_count_try == 0)) or (prev_count_try == 1 and prev_esito == 0 and time_difference > 360) or (time_difference > 600) or (current_serial != prev_serial):
        counter += 1
    
    group_counter.append(counter)  # Aggiungi il valore del contatore alla lista della nuova colonna

# Assegna la lista della nuova colonna al dataframe
df['count_Operation'] = group_counter
df.count_Operation.astype('int64')
# Raggruppo per ogni set di operazioni
grouped = df.groupby('count_Operation')
# Conto il numero di operazioni effettuate in ogni set
counts = grouped.size().reset_index(name='group_size')
# Aggiungo la colonna 'group_size' al DF per tenere traccia del numero di operazioni fatte in ogni set
df = df.merge(counts, on='count_Operation')

# Aggiungo una colonna 'Outcome' per vedere se all'interno di ogni set di operazioni
# le avvitature sono andate tutte a buon fine
# Outcome == True -> Tutte le avvitature all'interno del set andate ok
# Outcome == False -> C'è stato almeno un errore all'interno del set
df['Outcome'] = df['group_size'] == df['Batch']
    
# Aggiungo la colonna che tiene conto degli errori commessi qualora ce ne siano
df['Errors'] = df.group_size - df.Batch
df['Error_percentage'] = df['Errors'] / df['group_size'] * 100

# Droppo duplicati per creare il dataframe condensato
df_condensated = df.drop_duplicates('count_Operation')[['SerialNumber','Creation_date','Global_ID','Tool_ID','Pset_ID','Fase','Operatore','Batch','Outcome','Step_Instruction','group_size','StartTime','count_Operation','Errors','Error_percentage','File_path']]

# Dataframe con esiti positivi, per la stima dei tempi medi delle operazioni
df_condensated_done_op = df_condensated[df_condensated.Outcome == True].drop(['Errors','Error_percentage'],axis=1)#.reset_index()

# Prendo le avvitature (ogni singola) che hanno più di 1 tentativo effettuato
df_duration = df[(df.group_size > 1)][['SerialNumber','Creation_date','Global_ID','Tool_ID','Pset_ID','Fase','Operatore', 'Batch','Outcome','Step_Instruction','group_size','StartTime','count_Operation','Errors','Error_percentage','File_path']]

df_duration['meanDuration'] = df_duration.groupby('count_Operation')['StartTime'].diff().dt.total_seconds().astype('float64')
avg = df_duration.groupby('count_Operation')['meanDuration'].mean()
df_duration = df_duration.merge(avg, on = 'count_Operation')
df_duration['Duration'] = df_duration.groupby('count_Operation')['StartTime'].transform(lambda x: x.max()-x.min()).dt.total_seconds().astype('float64')

df_duration = df_duration.drop(['meanDuration_x'],axis=1)
df_duration = df_duration[~df_duration['count_Operation'].duplicated()]

df_duration.rename(columns = {'meanDuration_y': 'meanDuration'}, inplace=True)

df_duration = df_duration[['SerialNumber','Creation_date','Global_ID','Tool_ID','Pset_ID','Fase','Operatore','Batch','Outcome','Step_Instruction','group_size','StartTime','count_Operation','Errors','Error_percentage','Duration','meanDuration','File_path']]

df_duration.to_csv('Pset_DF_cond.csv',index=False)