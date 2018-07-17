import pickle, csv

path_db = 'data/'

def readconfig():
    with open('globals/' + 'authsms.pk', 'rb') as f:
	config = pickle.load(f)
	
    return config


def updatedb(data, filename):
##    data_db = readdb(filename) 
##    data_db.update(data)
    data_db = data  #************************
    with open(path_db+filename+'.db', 'wb') as db:
        pickle.dump(data_db, db)    

    return


def readdb(filename):
    try:
        with open(path_db+filename+'.db', 'rb') as db:
            data_db=pickle.load(db)
    except IOError:
        data_db={}
    except EOFError:
        data_db = {}
        
    return data_db


def translatekeys(logger, loggerdata={}): #from a csv (.dct) dictionary in globals
    reader=csv.reader(open('globals/'+logger+'.dct', 'rU').readlines(), delimiter=';', quotechar='"')
    translator={}
    data={}
    for lines in reader:
        dbheader=lines[0]
        if dbheader != '':
            translator[dbheader]=[]
            for langs in lines[1:]:
                translator[lines[0]].append(langs)

    for keys in translator:
        languages = translator[keys]
        for i in range(len(languages)):
            try:            
                data[keys]=loggerdata[languages[i]]
            except KeyError:
                pass
        
    return data

       
