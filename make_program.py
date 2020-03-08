import radiko_record

from tabulate import tabulate
import sqlite3
from datetime import datetime, date, timedelta

# TODO: 細かい入力の例外処理を行う
# TODO: 適切な場所で画面のフラッシュを行う
# TODO: tabulate が日本語に若干対応してなさそうなのに対応する

# ファイル名を含む場合
def show_record(Plist):
    headers = ['start','end','day','station','filename','name']
    week_daylist = ['月','火','水','木','金','土','日']

    table = []
    for i in Plist:
        name = i[0]
        filename = i[1]
        start = datetime.strptime(i[2], '%H%M%S').strftime('%H:%M')
        end = datetime.strptime(i[3], '%H%M%S').strftime('%H:%M')
        day = week_daylist[int(i[4])]
        station = i[5]

        info = [start, end, day, station, filename , name]
        table.append(info)

    result = tabulate(table, headers, tablefmt='github',stralign='left', showindex=True)
    print(result)

# ファイル名を含まない場合
def show_program(Plist):
    headers = ['start','end','day','station','name']
    week_daylist = ['月','火','水','木','金','土','日']

    table = []
    for i in Plist:
        name = i[0]
        start = datetime.strptime(i[1], '%H%M%S').strftime('%H:%M')
        end = datetime.strptime(i[2], '%H%M%S').strftime('%H:%M')
        day = week_daylist[int(i[3])]
        station = i[4]

        info = [start, end, day, station, name]
        table.append(info)

    result = tabulate(table, headers, tablefmt='github',stralign='left', showindex=True)
    print(result)

def show_program_list():
    conn = sqlite3.connect('./radiko.db')
    c = conn.cursor()

    c.execute("select name from sqlite_master where type='table'")
    table_is_exist = False
    for i in c.fetchall():
        if 'radio_program' in i:
            table_is_exist = True
    if not(table_is_exist):
        print('番組表がまだ作成されていません')
        return 

    c.execute("select title,filename,start,end,day,station from record_program")
    Plist = c.fetchall()
    show_record(Plist)
    c.close()
    conn.commit()
    conn.close()

def make_program_list():
    week_daylist = ['mon','tue','wed','thu','fri','sat','sun']

    conn = sqlite3.connect('./radiko.db')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS record_program(title,filename,start,end,day,station)")
    while(True):
        title = input('録音したい番組名> ')
        c.execute('select * from radio_program where title like ?',(['%'+title+'%']))
        Plist = c.fetchall()
        if Plist == []:
            print('その番組は見つかりませんでした')
            continue

        #for i,j in zip(Plist,range(len(Plist))):
        #    start = datetime.strptime(i[1], '%H%M%S').strftime('%H:%M')
        #    end = datetime.strptime(i[2], '%H%M%S').strftime('%H:%M')
        #    print(str(j)+'> title:"'+i[0]+'" time:"'+start+'~'+end+'" '+week_daylist[int(i[3])])
        show_program(Plist)

        prog_num = input('録音する番組番号(複数ある場合はスペースで)> ')
        prog_list = prog_num.split()
        if prog_list == []:
            print('入力がないのでやり直します')
            continue

        for i in prog_list:
            while True:
                content = Plist[int(i)]
                start = datetime.strptime(content[1], '%H%M%S').strftime('%H:%M')
                end = datetime.strptime(content[2], '%H%M%S').strftime('%H:%M')
                print('title:"'+content[0]+'" time "'+start+'~'+end+'" '+week_daylist[int(content[3])])
                filename = input('ファイル名> ')
                if filename == "":
                    continue
                else:
                    ContentList = list(content)
                    ContentList = ContentList[:1]+[filename]+ContentList[1:]
                    c.execute("INSERT INTO record_program VALUES(?,?,?,?,?,?)",(ContentList))
                    break

        c.close()
        conn.commit()
        conn.close()
        break

def delete_program_list():
    conn = sqlite3.connect('./radiko.db')
    c = conn.cursor()
    c.execute("SELECT * FROM record_program")
    Plist = c.fetchall()

    delnum = input("消去したい番号(-1でやめる)> ")
    if int(delnum) < 0:
        return 

    show_record([Plist[int(delnum)]])
    is_ok = input('以上を消去します．よろしいですか？(y/N)> ')
    if is_ok == 'y':
        c.execute("DELETE FROM record_program where title=(?) AND filename=(?) AND start=(?) AND  end=(?) AND day=(?) AND station=(?)", (Plist[int(delnum)]))
        
    c.close()
    conn.commit()
    conn.close()
        
def main():
    # make_programDB is very heavy operation 
    # so it has to be estimated it is needed or not.
    while(True):
        try:
            conn = sqlite3.connect('./radiko.db')
            c = conn.cursor()
            c.execute('SELECT date FROM radio_program')
            date = c.fetchone()[0]
            c.execute('select date from radio_program where date == 1')
            print(c.fetchone())
            c.close()
            conn.commit()
            conn.close()
        except sqlite3.Error: 
            print('getting program...')
            radiko_record.make_programDB()
        else:
            break

    date = datetime.strptime(date, '%Y%m%d%H%M')
    today = datetime.today()
    if today > date + timedelta(hours=3):
        print('getting program...')
        radiko_record.make_programDB()
    
    while True:
        show_program_list()
        select = input('''
1> 番組の登録
2> 番組の消去
3> 終了
>''')
        if select == '1':
            make_program_list()
        elif select == '2':
            delete_program_list()
            pass
        elif select == '3' or select == 'q':
            return 0
        else:
            print('1~3の数字を入力してください')
            continue

if __name__=="__main__":
    main()

