from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException        

from lxml import html,etree
import getpass
import json, time, os, csv, pickle,argparse,random
from sys import exit



MFACEBOOK_URL="https://m.facebook.com/"
FACEBOOK_PROFILE_URL='https://mbasic.facebook.com/profile.php?v=info&id='

FRIENDS_HTML=os.getcwd() + '/' + "friends.html"

DRIVER_NAME="chromedriver.exe"
DRIVER_DIR=os.path.join(os.getcwd(),DRIVER_NAME)

#element load timeout
TIMEOUT = 5


headers ={
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9", 
    "Accept-Encoding": "gzip, deflate, br", 
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7,ar;q=0.6", 
    "Host": "httpbin.org", 
    "Sec-Ch-Ua": "\"Google Chrome\";v=\"87\", \" Not;A Brand\";v=\"99\", \"Chromium\";v=\"87\"", 
    "Sec-Ch-Ua-Mobile": "?0", 
    "Sec-Fetch-Dest": "document", 
    "Sec-Fetch-Mode": "navigate", 
    "Sec-Fetch-Site": "none", 
    "Sec-Fetch-User": "?1", 
    "Upgrade-Insecure-Requests": "1", 
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36", 
    "X-Amzn-Trace-Id": "Root=1-6006dd63-4d1494383800f3186963da5c"
  }


def setup_driver(dir_driver):
    #webdriver options and config        

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    # chrome_options.add_argument("--headless")

    #Add headers
    for header in headers:
        chrome_options.add_argument(f"{header}={headers[header]}")
    
    driver = webdriver.Chrome(chrome_options=chrome_options)

    return driver

def signin(driver):
    fb_login = input('enter your fb login: ') 
    fb_pass = getpass.getpass(prompt='enter your fb password: ') 
    
    driver.get(MFACEBOOK_URL)
    
    #Wait for inputs
    WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.ID, 'm_login_email')))
    WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.ID, 'm_login_password')))
    WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.NAME, 'login')))


    email_id = driver.find_element_by_id("m_login_email")
    pass_id = driver.find_element_by_id("m_login_password")
    confirm_id = driver.find_element_by_name("login")
    
    email_id.send_keys(fb_login)
    pass_id.send_keys(fb_pass)
    confirm_id.click()
    
    print("Logging in automatically...")

    time.sleep(5)
    if "Log" in driver.title:
        print("Login failed pls check your credentials and retry")
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

def get_work(driver, parse):
    friend_work = []
    xpath = '//*[@id="work"]/div[1]/div/div'
    try:
        work_div = WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.ID, 'work')))
        work_list = parse.xpath(xpath)
        for i in range (1, len(work_list)+1):
                try:
                    work = parse.xpath(xpath+'['+str(i)+']'+'/div/div[1]//a')[0].text
                    friend_work.append(work)
                except:
                    pass
    except TimeoutException:
        print(f"Xpath work failed")

    if friend_work==[]:
        return False

    return ", ".join(friend_work)

def get_current_city(driver, parse):
    current_city=""
    xpath = "//*[contains(text(),'Current ')]//following::td//a"
    try:
        city_div = WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.ID, 'living')))
        current_city =parse.xpath(xpath)[0].text
    except TimeoutException:
        print(f"Xpath city failed")
        return False

    return current_city

def get_friend_info(driver,friend):

    friendId=friend["friendId"]
    friendName=friend["friendName"]
    
    infos={
        "full_name":friendName,
        "work":"",
        "current_city":""
    }

    driver.get(FACEBOOK_PROFILE_URL+str(friendId))   
    source_page = html.fromstring(driver.page_source)
    
    work = get_work(driver, source_page)
    current_city = get_current_city(driver, source_page)

    #return false if no info in both section 
    #it is either an error or just the user dont have data
    if (work==False and current_city==False):
        return False
    else:
        infos["work"]=work
        infos["current_city"]=current_city
        return(infos)


def load_parsed_friends():
    with open('parsed.pkl', 'rb') as f:
        parsed_ids = pickle.load(f)
    return parsed_ids

def save_parsed_friends(ids_list):
    with open('parsed.pkl', 'wb+') as f:
        pickle.dump(ids_list,f)

def restart_progress():
    save_parsed_friends([])
    info_file=open("friendsInfo.csv","r+")
    info_file.truncate(0)
    info_file.close

if __name__ == "__main__":

    args = argparse.ArgumentParser()
    args.add_argument("--restart", action="store_true", help="clear progress")
    args = args.parse_args()
    
    if args.restart:
        restart_progress()

    driver = setup_driver(DRIVER_NAME)
    if signin(driver):
        download_friends_list(driver, FRIENDS_HTML)
        
        ids_to_skip = load_parsed_friends()

        with open("friendsInfo.csv", 'a', encoding="utf-8", newline='') as f:
            fnames = ['full_name', 'work','current_city']
            writer = csv.DictWriter(f, fieldnames=fnames)    
            
            if len(ids_to_skip) == 0:
                writer.writeheader()

            try:
                for friend in get_friends_id(FRIENDS_HTML):
                    if not(friend["friendId"] in ids_to_skip):                        
                        print(f"\n>> Writing {friend['friendName']} 's infos \n (Ctrl+C to save your progress and exit)")
                        
                        #if there is no data skip the user
                        info=get_friend_info(driver,friend)
                        if info != False:
                            ids_to_skip.append(friend["friendId"])
                            writer.writerow(info)
                            print("Skipped!")
                        
                        #Generate random sleep time
                        time.sleep(random.randint(10,30))
                print(f"\n>> Completed! \n Saved to friendsInfo.csv")

            except (KeyboardInterrupt, EOFError):
                print(">>Progress saved")
                
            finally:
                print("Terminated, check the csv file")
                save_parsed_friends(ids_to_skip)
                driver.close()
                exit()





            





