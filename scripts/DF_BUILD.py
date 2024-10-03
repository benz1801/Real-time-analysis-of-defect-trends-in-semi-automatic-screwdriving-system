# PYTHON SCRIPT PER CREARE UN DATAFRAME DA UNA CARTELLA CONTENENTE DEI LOGFILES

# Useful Packages
import pandas as pd
import datetime
import timeit
import time
import os
import re
from tkinter import filedialog

# Funzione che ritorna una lista di informazioni data una loglines in input
def extract_info_without_brackets(string: str) -> list:
    Information = []
    splitted_list = string.split()           
    timeinfo = ' '.join(splitted_list[:2])
    Information.append(datetime.datetime.strptime(timeinfo,'%d/%m/%Y %H:%M:%S'))      #START_TIME         0
    Information.append(splitted_list[len(splitted_list)-1])                           #TOOL_ID            1
    Information.append(splitted_list[7][:3])                                          #PSET_ID            2
    Information.append(splitted_list[7][4])                                           #SUB_PROGRAM        3

    Tq_int = splitted_list[13][:6]  
    Information.append(float(Tq_int[:4] + '.' + Tq_int[4:]))                          #TQ                 4
    Information.append(splitted_list[13][7])                                          #ESITO_TQ           5
    Ag_int = splitted_list[15][:5]
    Information.append(float(Ag_int[:4] + '.' + Ag_int[4:]))                          #AG                 6
    Information.append(splitted_list[15][6])                                          #ESITO_AG           7
    Information.append(splitted_list[9][0:2])                                         #COUNT_TRY          8
    Information.append(splitted_list[9][3:5])                                         #BATCH              9
    Information.append(splitted_list[11])                                             #ESITO_FINALE       10
    Information.append(splitted_list[3])                                              #STEP_INSTRUCTION   11
    Information.append(9999)                                                          #colonna marco      12

    return(Information)  

# La stessa funzione ma nel caso di un altro formato delle loglines
def extract_info_with_brackets(string: str) -> list:
    Information = []
    splitted_list = string.split()            
    timeinfo = ' '.join(splitted_list[:2])
    Information.append(datetime.datetime.strptime(timeinfo,'%d/%m/%Y %H:%M:%S'))     #START_TIME         0
    Information.append(splitted_list[len(splitted_list)-1])                          #TOOL_ID            1
    Information.append(splitted_list[11][:3])                                        #PSET_ID            2
    Information.append(splitted_list[11][4])                                         #SUB_PROGRAM        3

    Tq_int = splitted_list[17][:6]  
    Information.append(float(Tq_int[:4] + '.' + Tq_int[4:]))                         #TQ                 4
    Information.append(splitted_list[17][7])                                         #ESITO_TQ           5
    Ag_int = splitted_list[19][:5]
    Information.append(float(Ag_int[:4] + '.' + Ag_int[4:]))                         #AG                 6
    Information.append(splitted_list[19][6])                                         #ESITO_AG           7
    Information.append(splitted_list[13][0:2])                                       #COUNT_TRY          8
    Information.append(splitted_list[13][3:5])                                       #BATCH              9
    Information.append(splitted_list[15])                                            #ESITO_FINALE       10
    Information.append(splitted_list[7])                                             #STEP_INSTRUCTION   11
    Information.append(splitted_list[5].strip('{}'))                                 #colonna marco      12

    return(Information) 

# Funzione che ritorna la data di creazione di un file passato in input
def creation_date(path_file: str) -> datetime.datetime:
    if not os.path.isabs(path_file):
        path_file = os.path.abspath(path_file)

    c_time = os.path.getctime(path_file)
    c_time_str = time.ctime(c_time)
    c_data = datetime.datetime.strptime(c_time_str[4:], '%b %d %H:%M:%S %Y')
    return c_data

# Funzione per buildare un DataFrame data una cartella contenente logfiles in input
def DF_BUILDING(directory: str) -> pd.DataFrame:
    start = timeit.default_timer() #per tenere conto del tempo di esecuzione

    PATH = os.path.abspath(directory)
    FILE_LIST = []
    for cartella, _ ,files in os.walk(PATH): #per navigare in ogni file dentro sottocartelle
        for file in files:
                if re.match(r"\d{10}\.txt", file) or re.match(r"t.*-IT\d+-\d+-\d+\.txt", file, re.IGNORECASE):
                #if re.match(r"\d{2}\d{2}.+\.txt", file) and len(re.findall(r"\d", file)) <= 10:
                    file_path = os.path.join(cartella,file)
                    FILE_LIST.append(file_path)
                #elif re.match(r"t.*-IT\d+-\d+-\d+\.txt", file, re.IGNORECASE):
                    #file_path = os.path.join(cartella,file)
                    #FILE_LIST.append(file_path)
    
    pathfile_time_tuples = []  #lista di tuple con pathfile e tempo di creazione
    file_time_tuples = []      #uguale ma invece del path assoluto solo il nome del file
    for file in FILE_LIST:
        c_data = creation_date(file)

        pathfile_time_tuples.append((file,c_data))
        file_time_tuples.append((os.path.basename(file),c_data))

    pathfile_time_dict = dict(pathfile_time_tuples)
    file_time_dict = dict(file_time_tuples)

    data1 = []
    txt = []
    
    # Insert in a 'txt' list each string lines of files in a folder
    for file in pathfile_time_dict:
        name_file = os.path.basename(file)
        with open(file, 'r') as f:
            txt.append(file)
            txt.append(name_file)
            txt.extend( f.readlines() ) 

    i = 0
    while i < len(txt):
        if txt[i].startswith('@'):
            Fase = txt[i].strip('@\n')
        
        elif os.path.isabs(txt[i]):
            File_path = os.path.abspath(txt[i])

        elif txt[i].startswith('Op:'):
            Operatore = txt[i].strip('Op: \n')
        
        elif '---' in txt[i]:
            Global_ID = txt[i].strip(' - \n')
        
        elif txt[i].endswith('.txt'):
            SerialNumber = txt[i][:-4]
            Creation_date = file_time_dict[txt[i]]

        elif 'W - Ps: ' in txt[i]:
            if '{' in txt[i]:
                Information1 = extract_info_with_brackets(txt[i])
            else:
                Information1 = extract_info_without_brackets(txt[i])
            Information1.extend([Global_ID,SerialNumber,Fase,Operatore,Creation_date,File_path])
        
            data1.append(Information1)

        i+=1

    df = pd.DataFrame(data1, columns=['StartTime', 'Tool_ID', 'Pset_ID', 'Sub_program','Tq', 'Esito_Tq', 'Ag',
                                        'Esito_Ag', 'count_Try','Batch','Esito_finale','Step_Instruction', 'colonna_marco',
                                        'Global_ID','SerialNumber','Fase','Operatore','Creation_date','File_path']
                                        )
    
    dtypes = {'SerialNumber':'category','Tool_ID':'category','Pset_ID':'category','Sub_program':'category',
              'Tq':'float64', 'Esito_Tq':'int64', 'Ag':'float64', 'Esito_Ag':'int64', 'count_Try':'int64',
              'Batch':'int64', 'Esito_finale':'int64', 'Step_Instruction':'int64', 'Global_ID':'category',
              'Fase':'category', 'Operatore':'category', 'colonna_marco':'int64', 'File_path':'str'
            }
    df = df.astype(dtypes)

    stop = timeit.default_timer()                                 
    print(f'Tempo di esecuzione per la costruzione del dataset: {stop-start:.2f} secondi')
    print('__________________________________________________________\n')

    
    return df

# Panoramica del dataframe generato
if __name__ == '__main__':
    df = DF_BUILDING(filedialog.askdirectory())
    print(' Una panoramica del dataframe:')
    print(df)
    print('__________________________________________________________\n')
    answer = input('Vuoi salvare il file? \n')
    if answer == 'si' or answer == 'Si' or answer == 'sI' or answer == 'SI':
        csv_name = str(input('Inserisci il nome del file che vuoi salvare: ') + '.csv')
        df.to_csv(csv_name)
    print(input("Premere INVIO per uscire..."))
    