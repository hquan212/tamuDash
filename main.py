# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from os import listdir
from os.path import isfile, join


def get_files(mypath):
    return [f for f in listdir(mypath) if isfile(join(mypath, f))][1:]

def convert_dollars_to_float(df, column):
        temp = df[column].str.replace('$', '')
        temp = temp.apply(lambda x: x.replace(',',''))
        temp = temp.replace('+/-', '')
        return temp.astype(float)

def main():
    res = pd.DataFrame({'Major' : [],	'Degree' : [],	'NumSalariesReported' : [],	'Avg' : [],	'Max' : [],	'Min' : [],	'StDev' : [],	'25th' : [],	'Median' : [],	'75th' : []})
    
    for file in get_files('raw/'):
        print(file)
        df = pd.read_csv('./raw/' + file)
        df.columns = ['Major',	'Degree',	'NumSalariesReported',	'Avg',	'Max',	'Min',	'StDev',	'25th',	'Median',	'75th']
        df['Year'] = file.split('_')[0]
        df['Semester'] = file.split('_')[1].replace('.csv', '')

        collegeNames = ['College of Agriculture & Life Sciences']
        indexPos = [0] + df[df['Max'].isna()].index.tolist() + [df.shape[0]]
        collegeNames += df[df['Max'].isna()]['Major'].tolist()

        # df[df['Max'].isna()] # Find all of the dataframe seperatations
        for i, idx in enumerate(indexPos[1:]):
            tempDF = None
            if (type(df.iloc[indexPos[i],4]) == float or df.iloc[indexPos[i],4] == np.nan):
                tempDF = df.iloc[(indexPos[i]+2):(idx-4), :]
            else:
                tempDF = df.iloc[(indexPos[i]+1):(idx-4), :]
            for column in ['Avg','Max','Min','25th','Median','75th']:
                tempDF[column] = convert_dollars_to_float(tempDF, column)
            tempDF['College'] = collegeNames[i]
            res = res.append(tempDF)
            res.reset_index(drop=True, inplace=True)

    res.to_csv('merged.csv')



if __name__ == "__main__":
    main()