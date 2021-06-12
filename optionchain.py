#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#jai guru dev
#om gam ganapataye namah
"""
Created on Fri May  8 00:33:36 2020

@author: varun
"""

import pandas as pd
import numpy  as np
from datetime import date, datetime, timedelta
import nsepython as nse
from sqlalchemy import create_engine

#def get_options(category,instrument):
def get_options(instrument):
    #global loc
    
    data_acc = nse.option_chain(instrument)
    
    try:  
        ce_r = [i['CE'] for i in data_acc['records' ]['data'] if "CE" in i]
        pe_r = [i['PE'] for i in data_acc['records' ]['data'] if "PE" in i]
    except KeyError:        
        ce_r = [i['CE'] for i in data_acc['filtered']['data'] if "CE" in i]
        pe_r = [i['PE'] for i in data_acc['filtered']['data'] if "PE" in i]
        
    ##create the full dataframe
    ce_r = pd.DataFrame(ce_r); pe_r = pd.DataFrame(pe_r)    
    ce_r['expiryDate'] = pd.to_datetime(ce_r['expiryDate'],format = '%d-%b-%Y')
    pe_r['expiryDate'] = pd.to_datetime(pe_r['expiryDate'],format = '%d-%b-%Y')
    ce_r = ce_r.set_index(['expiryDate','strikePrice'])    ; pe_r = pe_r.set_index(['expiryDate','strikePrice'])
    ce_r.columns = ['call_'+name for name in ce_r.columns] ; pe_r.columns = ['put_'+name for name in pe_r.columns]  
    df= pd.concat([ce_r,pe_r],axis=1,sort = False)
    
    ##select the rows
    expi = list(set([df.index[i][0] for i in range(len(df)) if df.index[i][0] < date(2021,6,30)]))
    uv = df['call_underlyingValue'].iloc[0]; uniq = [x[1] for x in df.index];uniq = list(set(uniq));uniq.sort()
    diff = int(uniq[1]-uniq[0]); uv =  int(round(uv/diff)*diff); 
    stri = [x for x in range(uv-diff*5,uv+diff*6,diff)]
    df = df.loc(axis=0)[expi, stri]
    
    ##select the columns
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S") ;  df['timestamp'] = ts   
    loc =[ 'timestamp', 'call_underlyingValue','call_openInterest','call_lastPrice','call_impliedVolatility','put_openInterest','put_lastPrice','put_impliedVolatility']
    df = df[loc]
    loc =['timestamp','value','call_OI','call_LP','call_IV','put_OI','put_LP','put_IV'] ; df.columns = loc
    
    # write the trimmed datframe to csv
    #df.to_csv(f'{instrument}_options.csv',mode='w',header = False)
    
    return df

def main():
    global instruments
    #global categories, data , main_dict2    
    #categories = {'equities':['AXISBANK','UPL'], 'indices':['NIFTY']}
    #data = {instrument:get_options(category,instrument) for category in categories for instrument in categories[category]}
    instruments = ['AXISBANK','UPL','NIFTY','ICICIBANK','SBIN','CADILAHC']
    data = {instrument:get_options(instrument) for instrument in instruments}
    engine = create_engine('postgresql://postgres:myPassword@localhost:5432/optionchain')
    [data[a].to_sql(a, engine,if_exists='append') for a in data]
    

if __name__ == '__main__':
    main()