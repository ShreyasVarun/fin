#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 12 14:24:38 2020

@author: varun
"""
#import re
from nsepy import get_history
from datetime import date
from datetime import timedelta
import pandas as pd



def get_data(stock,start,end):
    a,b,c = start
    x,y,z = end
    data = get_history(stock,start = date(a,b,c), end = date(x,y,z))
    print('data retrival done')
    return data

def input_dates():
    dates = {}  
    i = 1
    while True:
       try:
           i_num = input("Enter a date. (Enter N to exit): ")
           if i_num == "N" or i_num =="n":
               break
           else:
                dates[i] = date(int(i_num[-4:]),int(i_num[3:5]),int(i_num[0:2]))
                i += 1               
       except ValueError:
           print("Please enter date in dd-mm-yyyy only. example 23-04-2020")
    return dates

def final_code():    
    df = get_data('BAJFINANCE',(2019,4,12),(2020,4,10))
    specific_dates = input_dates()
    df_dict = {}
    doi = [-30, -10, -7 , -5, -3 , 0 , 3, 7, 10]
    for i in specific_dates:
        doi_lis = []    
        try:
            sp_date_loc = df.index.get_loc(specific_dates[i])
            cl_price = df.iloc[sp_date_loc][7]
            print(cl_price)
        except:
            break
              
        for da in doi:
            if da == 0:
                doi_lis.append(cl_price)
            else:
                sp_date_loc = sp_date_loc + da
                try:
                    cl_price_doi = df.iloc[sp_date_loc]['Close']
                    percent_change = round(((cl_price - cl_price_doi)/(cl_price))*100,1)
                    doi_lis.append(percent_change)
                except KeyError:
                    doi_lis.append('nan')
                
            
        df_dict[specific_dates[i]] = doi_lis
    
    df_final  = pd.DataFrame.from_dict(df_dict,orient = 'index', columns = doi)
    print(df_final)

final_df = final_code()
            