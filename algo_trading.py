
# print('om gam ganapataye namah\njai guru dev ')

from breeze_connect import BreezeConnect
import pandas as pd
import numpy as np
import talib
from datetime import datetime, timedelta
import json
import time
import pickle as pkl
import warnings
import ta


# Callback to receive ticks.
def on_ticks(ticks):
    global list_tick
    global dfticks
    list_tick.append(ticks)
    dfticks = pd.DataFrame(list_tick)
    dfticks = dfticks.set_index('datetime')
    dfticks.index = pd.DatetimeIndex(dfticks.index)

def get_data(interval = "1minute",stock_code = "CADHEA",product_type="cash",
            from_date = '2023-01-01', to_date = '2023-01-01'):
    global breeze

    start_time = 'T07:00:00.000Z';end_time   = 'T17:00:00.000Z'
    if from_date == '2023-01-01' and to_date == '2023-01-01':
        now = datetime.now()               
        from_date = str(now)[0:10] + start_time
        to_date   = str(now)[0:10] + end_time
    else:
        from_date = from_date + start_time
        to_date   = to_date + end_time
        
    hd = breeze.get_historical_data(interval=interval,from_date= from_date, to_date= to_date, 
                                    stock_code=stock_code, exchange_code="NSE", product_type=product_type)
   
    df_try = pd.DataFrame(hd["Success"])
    df_try = df_try.set_index('datetime')
    df_try.index = pd.DatetimeIndex(df_try.index)
    df_try = df_try[['open','high','low','close','volume']]
    df_try = df_try.iloc[1:] 
    df_try = df_try.astype(float)
    return df_try

def scalp_signal(df,per = 5):
    a = pd.Series(data=[df['close'].iloc[:per].mean()], index=[df['close'].index[per-1]])
    b = df['close'].iloc[per:].ewm(alpha=1.0/per,adjust=False,).mean()
    df['wild'] = pd.concat([a,b])
    df['ewm'] = df['close'].ewm(span=per,min_periods=0,adjust=False,ignore_na=False).mean()
    df['cross'] = df['ewm'] - df['wild']
    df['bu']=ta.volatility.BollingerBands(df['close'],window = per, window_dev = 2).bollinger_hband().round(2)
    df['bl']=ta.volatility.BollingerBands(df['close'],window = per, window_dev = 2).bollinger_lband().round(2)
    df['RSI'] = ta.momentum.rsi(df['close'],window = per).round(2)
    df['bol'] = df['bu'] - df['bl']   
    df['signal'] = np.where(((df['low']-df['bl'])<0.5)&(df['cross']>0)&(df['RSI']>50)&(df['RSI']<80),'buy',                            
                            np.where(((df['bu']-df['high'])>0.5)&(df['cross']<0)&
                            (df['close']>df['bl'])&(df['RSI']<50)&(df['RSI']>20),'sell',
                            np.NaN))
    df.drop(['ewm','wild'],axis=1,inplace=True)
    df = df.round(2)    
    return df

def trend_check(df5):
    df5 = df5.iloc[1:]
    df5['bu']=ta.volatility.BollingerBands(df5['close'],window = 5, window_dev = 2).bollinger_hband().round(2)
    df5['bl']=ta.volatility.BollingerBands(df5['close'],window = 5, window_dev = 2).bollinger_lband().round(2)
    df5['bol_dif'] = df5['bu'] - df5['bl']
    df5['bl_close']= np.where(((df5['close'] - df5['bl'])/df5['bol_dif'] < 0.1)&(df5['low']>df5['bl']),'down',
                     np.where(((df5['close'] - df5['bl'])/df5['bol_dif'] > 0.8)&(df5['high']<df5['bu']),'up','side'))
    return df5    
    
def assess_enter_exit(stock_code):
    print(f'a_e_e started at {datetime.now()}')
    global dfticks
    global breeze
    enter_order = False;entry_signal = False
    while True:
        # try:
        #     df_stock = dfticks.groupby('stock_code').get_group(stock_code)
        #     dfloat = df_stock[['open','high','low','close']].astype(float)
        #     df5min = dfloat.resample('5Min').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'})
        #     df1min = dfloat.resample('1Min').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'})
        #     break
        # except Exception as e:
        #     print (f'problem with tick data at data retrieval, with error {e}')            
        try:
            df5min = get_data(stock_code=stock_code,interval='5minute')
            df1min = get_data(stock_code=stock_code,interval='1minute')
            break
        except Exception as f:
            print(f'problem with get_data at data retrieval, with error {f}.sleeping for 10 sec')
            time.sleep(10)
            continue
            
    df5_live_trend  = trend_check(df5min)
    dfs_live = scalp_signal(df1min)           
    signal = dfs_live.tail(1)['signal'][0]
    five_min_trend = df5_live_trend.tail(1)['bl_close'][0]
    print(f'{five_min_trend = },{signal=}')

    if signal in ('buy','sell'):pass
    else:
        if np.random.random() > 0.5:signal = 'buy'
        else: signal = 'sell'   
    if five_min_trend in ('up','side') and signal == 'buy':
        entry_signal = True
        prev_cand = dfs_live.tail(6)
        enter = round(prev_cand.tail(1)['high'][0],1)
        stop_loss = round(prev_cand['low'].min(),1)
        exit_signal = 'sell'
    elif five_min_trend in ('down','side') and signal == 'sell':
        entry_signal = True
        prev_cand = dfs_live.tail(6)
        enter = round(prev_cand.tail(1)['low'][0],1)
        stop_loss = round(prev_cand['high'].max(),1)
        exit_signal = 'buy'
    else:pass

    if entry_signal:
        try:
            trade_amount = breeze.get_funds()['Success']['allocated_equity']
        except  Exception as g:
            print (g, ' at', datetime.now())
            trade_amount = 2800
        qty = round(trade_amount/enter); risk = enter - stop_loss
        book_profit = round(enter + risk * 1.5,1); book_profit2 = round(enter + risk * 3, 1)
        profit = round(abs(risk*1.5),2); risk = round(risk,2)        
        print(f'signal generated. risk and breakeven under evaluation')
        
        if  profit < (0.05/100) * enter:
            print( f"with {profit = } no breakeven, hence ignored\n")
        elif qty * abs(risk) > 2.5/100 * trade_amount:
            print(f"risk too high, {round(qty * abs(risk))}. Hence ignored.\n")            
        else:
            print (f' At {dfs_live.tail(1).index}, a {signal} signal was generated, with \
            {stop_loss = } and {book_profit = }\n')
            enter_order = True
    else:
        now2 = datetime.now()        
        if  750000 <= now2.microsecond <= 780000 and now2.second == 0:print(f'no signal at {now2}')
        else:pass
        return now2
    
    open_position = False
    if enter_order:        
        print(f'{signal=},{enter =},{qty =} ,{stop_loss = },{book_profit = }, {book_profit2 =}')
        entry_details = breeze.place_order(stock_code=stock_code,exchange_code="NSE",product="margin",
                    action=signal,order_type="limit",stoploss="",quantity=qty,price=enter,validity="day")        
        print(f"{entry_details =}") 
        entry_id = entry_details['Success']['order_id']

        while True:
            entry_status = breeze.get_order_detail(exchange_code="NSE", order_id=entry_id)
            entry_status = entry_status['Success'][0]['status']
            if entry_status == 'Executed':
                print('Entry complete!\n')
                open_position = True
                break
            else:
                print(f'order {entry_id} is placed, but not yet executed. waiting 10 seconds')
                time.sleep(10)
                continue        

        while True:
            try:
                df_stock_track = dfticks.groupby('stock_code').get_group(stock_code)
                td = (datetime.now() - df_stock_track.tail(1)['low'].index).seconds[0]
                if td > 10:
                    feed = breeze.subscribe_feeds(exchange_code="NSE", stock_code=stock_code, product_type="cash", expiry_date="", \
                        strike_price="", right="", interval="1second")                    
                    continue
                else:pass
                print(f'{df_stock_track.tail(1)["close"]=}\n')
                current_price = float(df_stock_track.tail(1)['low'][0])                
            except Exception as h: 
                feed = breeze.subscribe_feeds(exchange_code="NSE", stock_code=stock_code, product_type="cash", expiry_date="", \
                        strike_price="", right="", interval="1second")               
                print(f'the error at df stock track current price is {h}\n')                
                try:
                    df1min_live = get_data(stock_code=stock_code,interval='1minute')
                    print(f'{df1min_live.tail(1)["close"] = }\n')
                    current_price = df1min_live.tail(1)['low'][0]                    
                except Exception as i:                    
                    print(f'the error at df stock 1 min current price is {i}')                    
                    print('live price not retrived.. waiting 10 seconds\n')
                    time.sleep(10)
                    continue               
            print(f'entry position "{signal}", "{enter = }" still open, live = {current_price}, sl = {stop_loss}, bp ={book_profit}\n')
            
            sl_order = (exit_signal == 'buy'  and current_price>stop_loss) or \
                       (exit_signal == 'sell' and current_price<stop_loss)

            bp_order = (exit_signal == 'buy'  and current_price<book_profit) or \
                       (exit_signal == 'sell' and current_price>book_profit)
            
            if sl_order:
                exit_details = breeze.place_order(stock_code=stock_code,exchange_code="NSE",product="margin",
                    action=exit_signal,order_type="market",stoploss="",quantity=qty,price="",validity="day")

                exit_id = exit_details['Success']['order_id']
                exit_status = breeze.get_order_detail(exchange_code="NSE", order_id=exit_id)
                exit_status = exit_status['Success'][0]['status']  
                print(f'{exit_status = }')
                print(f' stoploss executed with {sl_order =} , {stop_loss =}, {current_price = }')
                break
            elif bp_order:
                exit_details = breeze.place_order(stock_code=stock_code,exchange_code="NSE",product="margin",
                    action=exit_signal,order_type="limit",stoploss="",quantity=qty,price=book_profit,validity="day")

                exit_id = exit_details['Success']['order_id']
                exit_status = breeze.get_order_detail(exchange_code="NSE", order_id=exit_id)
                exit_status = exit_status['Success'][0]['status']
                print(f'{exit_status = }')
                print(f'book profit executed with {bp_order =} , {book_profit =}, {current_price = }')
                break                
            else:
                exit_details = None
                continue
        
        while True:
            positions = breeze.get_portfolio_positions()
            print(f'{positions = }\n')
            if positions['Error'] == 'No Positions available.':
                print(f'All is well! at {datetime.now()}\n')
                open_position = False    
                break
            else:
                print(f'positions still open at, {datetime.now()}')
                time.sleep(10)
                continue               
    else:
        pass
    print(f'end of a_e_e at {datetime.now()}')
    return enter_order

def main():
    warnings.filterwarnings(action='ignore')
    global list_tick
    global breeze

    print(f'start of main at {datetime.now()}')

    breeze = BreezeConnect(api_key="0t244$67585!P03819jCN52)79o41205")
    breeze.generate_session(api_secret="32t3BV18423795Fy29K4n4om1D~37547",
                            session_token=3360341)

    breeze.ws_connect()
    list_tick = list()
    breeze.on_ticks = on_ticks
    stock_code = 'STABAN'
    feed = breeze.subscribe_feeds(exchange_code="NSE", stock_code=stock_code, product_type="cash", expiry_date="", \
                        strike_price="", right="", interval="1second")
    print(f'{feed =}')
    while True:
        assess_enter_exit(stock_code)
        print(f'at {datetime.now()}, bot is outside of "a_e_e". sleeping for 30 sec')
        time.sleep(30)
        if datetime.now().hour >= 15: break
        else:
            print(f'else coomand printed at {datetime.now()}')
            continue
        print('hello world')
        break
    

if __name__ == '__main__':
    main()



