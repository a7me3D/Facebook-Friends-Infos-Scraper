from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


from lxml import html,etree
import getpass
import json, time, os, csv

from io import BytesIO


MFACEBOOK_URL="https://m.facebook.com/"
BASICFACEBOOK_URL=""
DRIVER_NAME="chromedriver.exe"
FRIENDS_HTML=os.getcwd() + '/' + "friends.html"

DRIVER_DIR=os.path.join(os.getcwd()+"\\FacebookFriendsInfos\\src\\",DRIVER_NAME)

timeout = 5


def setup_driver(dir_driver):
    #webdriver options and config        
    headers = {'User-Agent': 'Mozilla/5.0(compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}

    chrome_options = Options()
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--headless")


    driver = webdriver.Chrome(chrome_options=chrome_options)

    return driver

def signin(driver):
    fb_login = input('enter your fb login: ') 
    fb_pass = getpass.getpass(prompt='enter your fb password: ') 
    driver.get(MFACEBOOK_URL)
    time.sleep(5)
    # email_present = EC.presence_of_element_located((By.ID, 'm_login_email'))
    # WebDriverWait(driver, timeout).until(email_present)
    email_id = driver.find_element_by_id("m_login_email")

    # pass_present = EC.presence_of_element_located((By.ID, 'm_login_password'))
    # WebDriverWait(driver, timeout).until(pass_present)
    pass_id = driver.find_element_by_id("m_login_password")
    
    # pass_present = EC.presence_of_element_located((By.ID, 'login'))
    # WebDriverWait(driver, timeout).until(pass_present)
    confirm_id = driver.find_element_by_name("login")
    
    email_id.send_keys(fb_login)
    pass_id.send_keys(fb_pass)
    confirm_id.click()
    
    print("Logging in automatically...")

    time.sleep(5)
    if "login" in driver.title.lower():
        print("login failed pls check your credentials and retry")
        return False

    return True


def download_friends_list(driver,friends_html):
    driver.get(MFACEBOOK_URL+"/me/friends")
    time.sleep(3)
    print('Loading friends list...')
    scrollpage = 1
    while driver.find_elements_by_css_selector('#m_more_friends'):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        scrollpage += 1
        time.sleep(0.5)

    with open (friends_html, 'w+', encoding="utf-8") as f:
        f.write(driver.page_source)


def get_friends_id(friends_html):
    html_friend_list = html.parse(friends_html).xpath
    xpath = '(//*[@data-sigil="undoable-action"])'
    friends_number = len(html_friend_list(xpath))
    for i in range(1,friends_number+1):
        friend_xpath = xpath + '['+str(i)+']/'
        friend_info = json.loads(html_friend_list(friend_xpath+'/div[3]/div/div/div[3]')[0].get('data-store'))
        friend_id = friend_info['id']
        friend_name = html_friend_list(friend_xpath+'/div[2]//a')[0].text
  
        yield({"friendName":friend_name,"friendId":friend_id})

def get_work(parse):
    friend_work = []
    xpath = '//*[@id="work"]/div[1]/div/div'
    work_list = parse.xpath(xpath)
    for i in range (1, len(work_list)+1):
        try:
            work = parse.xpath(xpath+'['+str(i)+']'+'/div/div[1]//a')[0].text
            friend_work.append(work)
        except:
            pass
    return friend_work

def get_current_city(parse):
    current_city=""
    xpath = "//*[contains(text(),'Current ')]//following::td//a"
    try:
        current_city =parse.xpath(xpath)[0].text
    except:
        pass
    return current_city

def get_friend_info(driver,friend):

    friendId=friend["friendId"]
    friendName=friend["friendName"]
    
    infos={
        "full_name":friendName,
        "work":"",
        "current_city":""
    }

    driver.get('https://mbasic.facebook.com/profile.php?v=info&id='+str(friendId))    
    source_page = html.fromstring(driver.page_source)

    work = get_work(source_page)
    infos["work"]=(work)

    current_city = get_current_city(source_page)
    infos["current_city"]=current_city
    
    return(infos)



if __name__ == "__main__":
    driver = setup_driver(DRIVER_NAME)
    if signin(driver):
        download_friends_list(driver, FRIENDS_HTML)
        with open("friendsInfo.csv", 'w', encoding="utf-8", newline='') as f:
            fnames = ['full_name', 'work','current_city']
            writer = csv.DictWriter(f, fieldnames=fnames)    
            writer.writeheader()
            for friend in get_friends_id(FRIENDS_HTML):
                info=get_friend_info(driver,friend)
                writer.writerow(info)
                print(f"\n>> Writing {friend['friendName']} 's infos")
                print(f"  info ")
                time.sleep(12)
            print(f"\n>> Completed! \n Saved to friendsInfo.csv")

        driver.close()




