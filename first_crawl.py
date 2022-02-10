from selenium import webdriver
import os
from time import sleep
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()

@sched.scheduled_job('cron', day_of_week='mon-sun', hour=1)

def scheduled_job():


    options = webdriver.ChromeOptions()
    options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    options.add_argument("--headless")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    browser = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=options)

    url = 'https://lmsone.iiitkottayam.ac.in/login/'
    browser.get(url)
    m_name = os.environ.get("MNAME")
    search = browser.find_element_by_name('username')
    m_pass = os.environ.get("MPASS")
    search.send_keys(m_name)
    search = browser.find_element_by_name('password')
    search.send_keys(m_pass)

    submit = browser.find_element_by_id('loginbtn')
    sleep(2)
    submit.click()
    sleep(5)

    url = 'https://lmsone.iiitkottayam.ac.in/calendar/view.php'
    browser.get(url)

    tasks = browser.find_elements_by_xpath('//h3[@class="name d-inline-block"]')
    t = []
    for i in tasks:
        t.append(i.text)

    def check(x):
        if x[0] not in ['Today,', 'Tomorrow,']: return True
        if x[0]=='Tomorrow,' and x[-1]=='PM': return True
        if x[0]=='Today': return False
        y = x[-2].split(':')
        if y[0] == '12': y[0] = '00'
        mins = int(y[0])*60 + int(y[1])
        if mins > 360: return True
        return False

    pending_assignments = browser.find_elements_by_xpath('//div[@class="description card-body"]//div[@class="row"]//div[@class="col-11"]')
    pending_assignments_name = browser.find_elements_by_xpath('//div[@class="description card-body"]//div[@class="row mt-1"]//div[@class="col-11"]//a')
    assignments = []
    for i in range(len(pending_assignments)):
        y = str(pending_assignments[i].text)
        y1 = str(pending_assignments_name[i].text)
        z = y.split()
        if check(z): break
        z.append(t[i])
        z.append(y1)
        assignments.append(z)


    d = dict()
    j = 1
    mail = ''
    for i in assignments:
        mail += (i[-1]+' : '+i[0]+' '+i[1]+' '+i[2]+' : '+i[-2]+"\n\n")
        j+=1


    if mail=='': mail="abhi checking chalu hai"
    d = {"task": mail}
    '''
    if mail:
        r = requests.post('https://hook.integromat.com/pxfywsoha4hey2h4hgyakhgicn7erj3h', data=json.dumps(d), headers={'Content-Type':'application/json'})
    '''

#------Mailing Scenes start here!!--------
    
    if mail:
        print("pikachu")
        recievers = []
        sheet_json = os.environ.get("JSON")
        spreadsheet_data = requests.get(sheet_json)
        spreadsheet_data = spreadsheet_data.json()

        for i in spreadsheet_data:
            if i['Select Yes/No.'] == 'Yes':
                recievers.append(i['Email Address'])

        for i in recievers:
            msg = MIMEMultipart()
            maill = os.environ.get("EMAIL")
            passs = os.environ.get("PASSWORD")
            msg['From'] = maill
            msg['To'] = i
            msg['Subject'] ="Assignemnts To Be Submitted Today!"
            body = 'Hello,\nThe assignments that require your attention today are listed below\n\n'+mail+'\n\nRegards.'
            msg.attach(MIMEText(body, 'plain'))
            text = msg.as_string()
            smtp_server = os.environ.get("SMTP_SERVER")
            sm= smtplib.SMTP(smtp_server, 587)
            sm.starttls()
            sm.login(maill, passs)
            sm.sendmail(maill, i, text)
            sm.quit()
    

sched.start()