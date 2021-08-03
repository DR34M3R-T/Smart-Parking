#!/usr/bin/python3
import tkinter as tk
from cv2 import VideoCapture,resize,cvtColor,COLOR_BGR2RGBA,CAP_DSHOW,CAP_PROP_FRAME_HEIGHT,CAP_PROP_FRAME_WIDTH
import threading
from requests import get,post
from base64 import b64encode
from PIL import Image, ImageTk#图像控件
from io import BytesIO
import pandas as pd
import datetime
import numpy as np
import matplotlib
from matplotlib import pyplot as plt
matplotlib.use('Agg')
import openpyxl

#excel processor
def file_save(df):
    lots_info=pd.read_excel('data\\data.xlsx',engine='openpyxl',sheet_name='lots_info')
    writer=pd.ExcelWriter('data\\data.xlsx',engine='openpyxl')
    df.to_excel(writer,sheet_name='cars_info',index=False)
    lots_info.to_excel(writer,sheet_name='lots_info',index=False)
    writer.save()

def car_check(car_id):
    if car_id==False:
        return False
    df = pd.read_excel('data\\data.xlsx',engine='openpyxl')
    #筛选status为True的car_id车辆
    t=datetime.datetime.now()
    df_in=df['status']
    df_id=df['car_id']==car_id
    df_filter=df_id & df_in
    if df_filter.sum()==0:
        if get_lots()==0:
            return -2,t.strftime("%Y-%m-%d %H:%M:%S"),car_id,-1
        add=pd.Series((car_id,True,t.strftime("%Y-%m-%d %H:%M:%S"),'','',''),index=df.columns)
        df=df.append(add,ignore_index=True)
        file_save(df)
        counter()
        return -1,t.strftime("%Y-%m-%d %H:%M:%S"),car_id,-1
    else:
        df.loc[df_filter,'status']=False
        df.loc[df_filter,'out_time']=t.strftime("%Y-%m-%d %H:%M:%S")
        t_in=str(df.loc[df_filter,'in_time'].values[0])
        try:
            t_in=datetime.datetime.strptime(t_in,"%Y-%m-%d %H:%M:%S")
        except:
            t_in=datetime.datetime.strptime(t_in,"%Y-%m-%dT%H:%M:%S.000000000")
        delta=t-t_in
        span=(delta.seconds//3600,(delta.seconds-delta.seconds//3600*3600)//60)
        df.loc[df_filter,'span']=str(span)
        global config
        fee=delta.seconds//1800*config['priceper30m']+config['priceper30m']#时间提取 费用计算
        df.loc[df_filter,'fee']=fee
        file_save(df)
        return fee,t_in.strftime("%Y-%m-%d %H:%M:%S"),car_id,span[0],span[1]

def car_sort():
    df = pd.read_excel('data\\data.xlsx',engine='openpyxl')
    df.sort_values(by=['status','in_time','out_time'],inplace=True,ascending=False)
    file_save(df)

def get_longest():
    t=datetime.datetime.now()
    df = pd.read_excel('data\\data.xlsx',engine='openpyxl')
    df.sort_values(by='in_time',inplace=True,ascending=False)
    df_in=df['status']
    t_in=df.loc[df_in,['car_id','in_time']]
    t_in.sort_values(by='in_time',inplace=True)
    try:
        car_id=t_in.iloc[[0],[0]].values[0][0]
        t_in=str(t_in.iloc[[0],[1]].values[0][0])
        try:
            t_in=datetime.datetime.strptime(t_in,"%Y-%m-%d %H:%M:%S")
        except:
            t_in=datetime.datetime.strptime(t_in,"%Y-%m-%dT%H:%M:%S.000000000")
        delta=t-t_in
        span=(delta.days*24+delta.seconds//3600,(delta.seconds-delta.seconds//3600*3600)//60)
        return car_id,span[0],span[1]
    except:
        return -1
    #df.to_excel('data\\data.xlsx',engine='openpyxl',index=False)

def get_lots():
    df = pd.read_excel('data\\data.xlsx',engine='openpyxl')
    lots_in=df['status'].sum()
    return 100-lots_in

def get_parkers():
    df = pd.read_excel('data\\data.xlsx',engine='openpyxl')
    df.sort_values(by='in_time',inplace=True,ascending=False)
    df_in=df['status']
    parkers=df.loc[df_in,['car_id','in_time']].values
    lenth=len(parkers)
    for i in range(lenth):
        parkers[i][1]=str(parkers[i][1])
    return parkers

def file_create():
    try:
        df=pd.read_excel('data\\data.xlsx',engine='openpyxl')
    except:
        writer=pd.ExcelWriter('data\\data.xlsx',engine='openpyxl')
        df=pd.DataFrame(columns=['car_id','status','in_time','out_time','fee','span'])
        df2=pd.DataFrame(columns=['date','weekday','total','max'])
        df.to_excel(writer,sheet_name='cars_info',index=False)
        df2.to_excel(writer,sheet_name='lots_info',index=False)
        writer.save()

def counter():
    lots_in=100-get_lots()
    df = pd.read_excel('data\\data.xlsx',engine='openpyxl')
    lots_info=pd.read_excel('data\\data.xlsx',engine='openpyxl',sheet_name='lots_info')
    date=datetime.datetime.now()
    lots_filter=lots_info['date']==str(date.date())
    if lots_filter.sum()==0:
        add=pd.Series((str(date.date()),date.weekday()+1,1,lots_in),index=lots_info.columns)
        lots_info=lots_info.append(add,ignore_index=True)
    else:
        lots_max=lots_info.loc[lots_filter,'max'].values[0]
        lots_info.loc[lots_filter,'total']+=1
        if lots_max<lots_in:
            lots_info.loc[lots_filter,'max']=lots_in
        pass
    writer=pd.ExcelWriter('data\\data.xlsx',engine='openpyxl')
    df.to_excel(writer,sheet_name='cars_info',index=False)
    lots_info.to_excel(writer,sheet_name='lots_info',index=False)
    writer.save()
    pass

def lots_warning():
    lots_info=pd.read_excel('data\\data.xlsx',engine='openpyxl',sheet_name='lots_info')
    date=datetime.datetime.now().date()
    date+=datetime.timedelta(1)
    date_list=[]
    delta=datetime.timedelta(-7)
    global config
    span=config['warn_source_span']
    if span==0:
        return False
    for i in range(span):
        date=date+delta
        date_list.append(str(date))
    date_filter=lots_info['date']==date_list[0]
    for j in range(span):
        date_filter|=lots_info['date']==date_list[j]
    num=date_filter.sum()
    if num==0:
        return False
    total_expect=lots_info.loc[date_filter,'total'].sum()/num
    max_expect=lots_info.loc[date_filter,'max'].sum()/num
    if total_expect>config['warn_total'] or max_expect>config['warn_max']:
        return True
    else:
        return False

def draw_chart():
    df = pd.read_excel('data\\data.xlsx',engine='openpyxl')
    df.sort_values(by='in_time',inplace=True,ascending=False)
    df_in=df['status']==False
    parkers=df.loc[df_in,['fee','in_time']].values
    lenth=len(parkers)
    for i in range(lenth):
        parkers[i][1]=str(parkers[i][1])
        parkers[i][1]=datetime.datetime.strptime(parkers[i][1],"%Y-%m-%d %H:%M:%S").month
    profit=[0,0,0,0,0,0,0,0,0,0,0,0]
    months=['一月','\n二月','三月','\n四月','五月','\n六月','七月','\n八月','九月','\n十月','十一月','\n十二月']
    for j in range(lenth):
        profit[parkers[j][1]-1]+=parkers[j][0]
    #指定默认字体
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']
    matplotlib.rcParams['font.family']='sans-serif'
    #解决负号’-‘显示为方块的问题
    matplotlib.rcParams['axes.unicode_minus'] = False
    fig, ax = plt.subplots(figsize=(4,5))
    ax.bar(x=months,height=profit,width=0.9)
    ax.set_title("月销售量统计图",fontsize=15)
    xticks = ax.get_xticks()
    m=max(profit)
    for i in range(len(profit)):
        xy = (xticks[i], profit[i]+m*1.01-m)
        s = str(profit[i])
        ax.annotate(
            text=s,  # 要添加的文本
            xy=xy,  # 将文本添加到哪个位置
            fontsize=8,  # 标签大小
            color="black",  # 标签颜色
            ha="center",  # 水平对齐
            va="baseline"  # 垂直对齐
        )
    buffer = BytesIO()
    fig.canvas.print_png(buffer)
    return buffer

def config_get():
    def raise_error(err_str):
        top = tk.Tk()
        top.geometry('0x0+999999+0')
        tk.messagebox.showerror(title='错误', message=err_str)
        top.destroy()
        quit()
    def cam_test(cam_id):
        try:
            cap = VideoCapture(cam_id,CAP_DSHOW)
        except:
            cap = VideoCapture(0,CAP_DSHOW)
        ret,img = cap.read()
        if type(img)!=np.ndarray:
            return False
        else:
            return True
    try:#文件是否存在
        f=open('data\\config.txt')
    except:
        raise_error('丢失config.txt或无权读取')
    try:#文件格式是否正确
        config=eval(f.read())
    except:
        f.close()
        raise_error('config.txt格式不正确')
    f.close()
    if type(config==dict):#文件格式是否正确
        dict_check=[['warn_source_span',2,int],
                    ['warn_max',80,int,float],
                    ['warn_total',200,int,float],
                    ['priceper30m',1.5,float,int]]
        for i in dict_check:#检查除camid外的数值项，若非法直接替换为默认值
            try:
                if config[i[0]]<0 or (type(config[i[0]]) not in i):
                    config[i[0]]=i[1]
            except:
                config[i[0]]=i[1]
        try:#检查camid
            temp=config['camera_id']
        except:
            config['camera_id']==0
        if not cam_test(config['camera_id']):
            raise_error('您的设备没有摄像头\n或者您输入了错误的camera_id')
        try:#检查key
            host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id='+config['API_KEY']+'&client_secret='+config['SECRET_KEY']
            response = get(host)
            access_token = False
            if response:
                access_token=eval(response.text)
                access_token=access_token['access_token']
            if access_token==False:
                raise_error('无效的API_KEY或SECRET_KEY')
        except:
            raise_error('无效的API_KEY或SECRET_KEY')
    else:
        raise_error('config.txt格式不正确')
    return config,access_token#返回config及token

#config get
config,access_token=config_get()
#open/create files
file_create()

def ocr(img):
    request_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/license_plate"
    # 二进制方式打开图片文件
    img = b64encode(img)
    params = {"image":img}
    request_url = request_url + "?access_token=" + access_token
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    response0 = post(request_url, data=params, headers=headers)
    car_id=False
    try:
        if response0:
            car_id=eval(response0.text)
            car_id=car_id['words_result']['number']
    except:
        car_id=False
    return car_id

def cam():
    global config
    try:
        cap = VideoCapture(config['camera_id'],CAP_DSHOW)
    except:
        cap = VideoCapture(0,CAP_DSHOW)
    cap.set(CAP_PROP_FRAME_WIDTH,3000)
    cap.set(CAP_PROP_FRAME_HEIGHT,3000)
    ret,img = cap.read()
    py=img.shape[0]
    px=img.shape[1]
    if px/700 > py/500:
        fy=fx=500/py
        cutterx=(px*fx-700)/2
        cuttery=0
    else:
        fy=fx=700/px
        cuttery=(py*fy-500)/2
        cutterx=0
    dsize=(int(px*fx),int(py*fy))
    global CAP_FLAG
    CAP_FLAG=CAP_FLAG
    notend=True
    while notend:
        ret, img = cap.read()#翻转 0:上下颠倒 大于0水平颠倒
        img = resize(img,dsize)
        img = cvtColor(img, COLOR_BGR2RGBA)
        img = Image.fromarray(img)
        img = img.crop((cutterx,cuttery,cutterx+700,cuttery+500))
        if CAP_FLAG:
            tr_cp=threading.Thread(target=capture,args=(img,))
            tr_cp.start()
            CAP_FLAG=False
        img=ImageTk.PhotoImage(img)
        id=camera.create_image(0,0,anchor='nw',image=img)
        camera.delete(id-1)
        camera.image=img
        global NOT_END
        notend=NOT_END
        #no_flash=img
    NOT_END=-1
    cap.release()

def capture(img):
    cap.config(state=tk.DISABLED)
    bytesIO = BytesIO()
    img.save(bytesIO, format='png')
    img=bytesIO.getvalue()
    car_id=ocr(img)##input('input car_id:')##
    renew_msg(car_check(car_id))
    renew_lots()
    renew_msg0()
    renew_parkers()
    car_sort()
    global WIN_FLAG
    if WIN_FLAG==1:
        WIN_FLAG=0
        show_profit()
    cap.config(state=tk.NORMAL)
def cap_():
    global CAP_FLAG
    CAP_FLAG=True

def show_profit():
    profit_info.config(state=tk.DISABLED)
    global WIN_FLAG
    if WIN_FLAG==0:
        win.geometry('1400x502')
        src=draw_chart()
        img=Image.open(src)
        img=img.resize((400, 500))
        #img.save('test.png')
        img=ImageTk.PhotoImage(image=img)
        profit_canvas.create_image(0,0,anchor='nw',image=img)
        profit_canvas.image=img
    else:
        win.geometry('1000x502')
        profit_canvas.delete('all')
    WIN_FLAG=1-WIN_FLAG
    profit_info.config(state=tk.NORMAL)

def renew_lots():
    for widget in lots_frame.winfo_children():
        widget.destroy()
    all_lots=100
    lots=get_lots()
    lots_str='共有车位：{}，现存车位：{}'
    remain_lots=tk.Label(lots_frame,text=lots_str.format(all_lots,lots),font=('微软雅黑',14),bg='#6699ff')
    remain_lots.pack()

def renew_msg0():
    for widget in msg_frame0.winfo_children():
        widget.destroy()
    temp=get_longest()
    if temp!=-1:
        msg0_str='停车时间最长车辆：{}\n已停车时长：{}小时{}分'
        msg0=tk.Label(msg_frame0,text=msg0_str.format(temp[0],temp[1],temp[2]),font=('微软雅黑',10),bg='#6699ff')
    else:
        msg0=tk.Label(msg_frame0,text='停车场暂无车辆',font=('微软雅黑',10),bg='#6699ff')
    msg0.pack()
def auto_renew_msg0():
    renew_msg0()
    win.after(30000,auto_renew_msg0)

def renew_msg(tuple):
    for widget in msg_frame.winfo_children():
        widget.destroy()
    if tuple==False:
        msg_str='未识别到有效车牌信息！'
        msg=tk.Label(msg_frame,text=msg_str,font=('微软雅黑',10),bg='#6699ff')
    else:
        msg_str='车牌号：{}\n'
        if tuple[0]==-2:
            msg_str+='本停车场已无空余车位！'
            msg=tk.Label(msg_frame,text=msg_str.format(tuple[2]),font=('微软雅黑',10),bg='#6699ff')
        elif tuple[0]==-1:
            msg_str+='有空余车位，可以进场停车\n进入停车场时间：{}'
            msg=tk.Label(msg_frame,text=msg_str.format(tuple[2],tuple[1]),font=('微软雅黑',10),bg='#6699ff')
        else:
            msg_str+='停车时长：{}小时{}分钟\n停车费：{}元\n离开停车场时间：{}\n'
            msg=tk.Label(msg_frame,text=msg_str.format(tuple[2],tuple[3],tuple[4],tuple[0],tuple[1]),font=('微软雅黑',10),bg='#6699ff')
    msg.pack()

def renew_parkers():
    parkers_body.delete('all')
    #获取车辆信息
    id=0
    for i in get_parkers():
        parkers_body.create_text(10, id*30+2, anchor=tk.NW, text=i[0],font=('微软雅黑',10))#window=info1)
        parkers_body.create_text(115, id*30+2, anchor=tk.NW, text=i[1],font=('微软雅黑',10))#window=info2)
        id+=1
    parkers_body.config(scrollregion=(0, 0, 280, 30*id+2))
    pass

def scroll_event(event):
    number = int(-event.delta / 120)
    parkers_body.yview_scroll(number, 'units')

def closeWindow():
    global NOT_END
    NOT_END=False
    def run():
        while NOT_END!=-1:
            pass
        win.quit()
    ex=threading.Thread(target=run)
    ex.start()

#window init
win = tk.Tk()
win.title('Smart Parking System')
win.geometry('1000x502')
win.resizable(0,0)
win.protocol('WM_DELETE_WINDOW', closeWindow)
#global flag
WIN_FLAG=0
NOT_END=True
CAP_FLAG=False
#camara panel init
camera_frame=tk.Frame(win,width=700,height=500,bd=-1)
camera=tk.Canvas(camera_frame,bg='white',width=700,height=500)
cap=tk.Button(camera_frame,text='捕获车牌号',command=cap_)
camera_frame.pack_propagate(0)
camera_frame.place(x=0,y=0,anchor='nw')
camera.pack(side='top')
cap.place(x=700,y=500,anchor='se')
if lots_warning():
    lots_warning=tk.Label(camera_frame,bg='white',text='明日车位情况可能比较紧张，请提前做好调度准备！',font=('微软雅黑',18))
    lots_warning.place(x=20,y=20,anchor=tk.NW)
#camera thread
tr_cam=threading.Thread(target=cam)
tr_cam.start()
#Info panel init
info_frame=tk.Frame(win,width=300,height=500,bg='#6699ff',bd=0)
info_frame.pack_propagate(0)
info_frame.place(x=1000,y=0,anchor='ne')
lots_frame=tk.Frame(info_frame,width=280,height=50,bg='#6699ff')
lots_frame.pack_propagate(0)
lots_frame.pack()
parkers_frame=tk.Frame(info_frame,width=280,height=250,bg='#6699ff')
parkers_frame.pack_propagate(0)
parkers_frame.pack()
parkers_head=tk.Frame(parkers_frame,width=280,height=30,bg='#6699ff')
parkers_head.grid_propagate(0)
parkers_head.pack()
header1=tk.Label(parkers_head,text='车牌号',font=('微软雅黑',13,'bold'),padx=20,bg='#6699ff')
header2=tk.Label(parkers_head,text='停入时间',font=('微软雅黑',13,'bold'),padx=54,bg='#6699ff')
header1.grid(row=0,column=0)
header2.grid(row=0,column=1)
parkers_scroll=tk.Scrollbar(parkers_frame,width=16,bg='#6699ff',orient='vertical',bd=0)
parkers_scroll.grid_propagate(0)
parkers_scroll.pack(side='right',fill=tk.Y)
parkers_body=tk.Canvas(parkers_frame,bg='#6699ff',bd=0)
parkers_body.pack(expand=True,fill='both')
parkers_body.config(yscrollcommand=parkers_scroll.set)
parkers_body.bind("<MouseWheel>", scroll_event)
parkers_scroll.config(command=parkers_body.yview)
msg_frame0=tk.Frame(info_frame,width=290,height=50,bg='#6699ff')
msg_frame0.pack_propagate(0)
msg_frame0.pack()
msg_frame=tk.Frame(info_frame,width=280,height=130,bg='#6699ff')
msg_frame.pack_propagate(0)
msg_frame.pack()
profit_info=tk.Button(info_frame,text='收入统计',command=show_profit)
profit_info.place(x=298,y=500,anchor='se')
profit_canvas=tk.Canvas(win,width=400,height=500,bg='white')
profit_canvas.place(x=1401,y=0,anchor='ne')
#info init
car_sort()
renew_lots()
auto_renew_msg0()
renew_parkers()
#main loop start
win.mainloop()