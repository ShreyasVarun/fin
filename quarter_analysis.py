#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 12 14:24:38 2020

@author: varun
"""
import re
from nsepy import get_history
from datetime import date
#from datetime import delta
def nsepy_data(stock,start,end):
    data = get_history(symbol = stock, start = start, end = end)
    return data

# define Python user-defined exceptions
class DdmmyyyyError(Exception):
   """Base class for other exceptions"""
   pass

#df = get_history('BAJFINANCE',date(2019,4,12), date(2020,4,12))
df2 = df
def input_dates():
    
    while True:
       try:
           i_num = input("Enter a date. (Enter N to exit): ")
           if i_num == "N" or i_num =="n":
               break
           else:
               if re.search(r'\d\d-\d\d-\d\d\d\d',i_num):
                   pass
               else:
                   raise DdmmyyyyError
               
       except DdmmyyyyError:
           print("Please enter date in dd-mm-yyyy only. example 23-04-2020")
           print()
