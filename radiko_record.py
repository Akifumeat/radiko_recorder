import requests
import base64
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta
import sqlite3
import ffmpeg
import subprocess

def get_authtoken():
    # key の取得もやってみたい
    key = 'bcd151073c03b352e1ef2fd66c32209da9ca0afa' 
    auth1_url = 'https://radiko.jp/v2/api/auth1'
    auth2_url = 'https://radiko.jp/v2/api/auth2'
    header = { 
            'X-Radiko-App':'pc_html5',
            'X-Radiko-App-Version':'4.0.0',
            'X-Radiko-User':'mankind',
            'X-Radiko-Device':'pc'
            }

    # first authentication 
    res = requests.get(auth1_url, headers=header)
    authtoken = res.headers['X-Radiko-AuthToken']
    keylen = int(res.headers['X-Radiko-KeyLength'])
    keyoffset = int(res.headers['X-Radiko-KeyOffset'])
    tmp = key[keyoffset:keyoffset+keylen]
    partialkey = base64.b64encode(tmp.encode('utf-8')).decode('utf8')

    # second authentication
    header = {
            'X-Radiko-AuthToken':authtoken,
            'X-Radiko-PartialKey':partialkey,
            'X-Radiko-User':'mankind',
            'X-Radiko-Device':'pc'
            }
    res = requests.get(auth2_url, headers=header)

    # TODO: Slack でエラーを送れるようにする
    if res.status_code != 200:
        print('authentication failed')
        exit(1)

    return authtoken

def record_radio(title,start,end,station): 
    date = datetime.strptime(start,'%Y%m%d%H%M%S').strftime('%Y%m%d')
    url = 'https://radiko.jp/v2/api/ts/playlist.m3u8?station_id='+station+'&l=15&ft='+start+'&to='+end
    authtoken = get_authtoken()

    (
            ffmpeg
            .input(url, **{'headers':"X-Radiko-AuthToken:"+authtoken})
            .output(title+'_'+date+".m4a",**{'bsf:a':"aac_adtstoasc","acodec":'copy'})
            .overwrite_output()
            .run()
    )

def make_programDB():
    # This is Only for Saitama.
    # JP+Prefecturecode is neeeded.
    # Please see 'http://nlftp.mlit.go.jp/ksj/gml/codelist/PrefCd.html'
    station_url = 'http://radiko.jp/v3/program/now/JP11.xml'
    url = 'http://radiko.jp/v3/program/station/date/'

    # get station id list
    res = requests.get(station_url)
    soup = BeautifulSoup(res.text, 'lxml-xml')
    tag = soup.find_all('station')
    station_list = []
    for i in tag:
        station_list.append(i.get('id'))

    # use sqlite
    conn = sqlite3.connect('radiko.db')
    c = conn.cursor()
    # this function shuld be called so as to create new table.
    c.execute('DROP TABLE IF EXISTS radio_program')
    c.execute('CREATE TABLE radio_program(title,start,end,day,station,PRIMARY KEY(title,start,end,day,station))')

    #get radio program title and time from start to end 
    today = datetime.today()
    for i in station_list:
        for j in range(7):
            date_str = (today + timedelta(days=j)).strftime("%Y%m%d")
            res = requests.get(url+date_str+'/'+i+'.xml')
            if res.status_code != 200:
                print('Something happend in getting radio program.')
                exit(-1)

            soup = BeautifulSoup(res.content, 'lxml-xml')
            title_list = soup.find_all('title')
            prog_list = soup.find_all('prog')
            for title,prog in zip(title_list, prog_list):
                title = title.string
                start = datetime.strptime(prog.get('ft'), '%Y%m%d%H%M%S')
                end = datetime.strptime(prog.get('to'), '%Y%m%d%H%M%S')
                weekday = start.weekday()

                # radio_program(title,start,end,day,station)
                c.execute('INSERT INTO radio_program values(?,?,?,?,?)',([title,start.strftime('%H%M%S'),end.strftime('%H%M%S'),weekday,i]))

    conn.commit()
    conn.close()

   
if __name__=="main":
    # __debug__
    #get_authtoken()
    #make_programDB()
    record_radio('a','20200201113456','20200201120000','BAYFM78')

