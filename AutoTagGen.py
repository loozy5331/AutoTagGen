from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from PIL import Image

import os
import time
import random
from io import BytesIO

class AutoGenStatus:
    """
        AutoTagGen의 status를 결정하기 위한 클래스
        self.ver_align : 세로로 중앙 정렬 유무. line-height로 처리. defualt is True
        self.hor_align : 가로로 중앙 정렬 유무. text-align으로 처리. default is True
        self.inner_text: innerText로 사용할 문구. default is "hello world"
    """
    def __init__(self, ver_align:bool=True, hor_align:bool=True, inner_text:str="hello world"):
        self.ver_align = ver_align
        self.hor_align = hor_align
        self.inner_text = inner_text

class AutoTagGen:
    """
        테스트 데이터를 생성하기 위해 비교적 단순한 태그들을 캡쳐해주는 클래스
        data에 관한 정보는 data/total_data.txt 에 저장된다.
        capture 된 이미지는 images/ 폴더 안에 저장된다.

        (기능) 특정 css prop를 고정하고, 그 외의 css prop를 변경(random.choice)하여 저장
        (제한 사항) 저장형식은 2d array 형식이고, 맨 위에는 해당 column의 데이터가 저장되게 된다.       

        self.driver : selenium chrome driver
        self.static_css_prop_val : 고정되어 사용하기 위한 css_prop_val {"css_prop":"css_value"}.     difault is dict()
                                     ex) { "height": "2px"}
        self.dynamic_css_props : 동적으로 할당되는 css props와 values {"css_prop": (min, max, interval) }.     difault is dict()
                                    ex) { "height": (100, 200, 1)}
        self.status : 기본으로 가지는 속성들
        self.gen_count : image를 생성할 갯수/ difault is 5
        self.total_data_dict : 전체 데이터를 가지고 있는 dictionary. 
                                 ex) {"height":{"img_1000.png":"3px", ...}, "width":{"img_10203.png":"300px", ...}}
    """
    def __init__(self, dynamic_css_props:dict=dict(), static_css_prop_val:dict=dict(), status:AutoGenStatus=AutoGenStatus(), gen_count:int=5):
        self.driver = self._get_driver()
        self.static_css_prop_val = static_css_prop_val
        self.dynamic_css_props = dynamic_css_props                                      
                                                                                                                 
        self.status = status
        self.gen_count = gen_count
        self.total_data_dict = self._load_data()
    
    # status에 의한 초기 설정
    def _set_status(self):
        if self.status.inner_text:
            self.driver.execute_script(f"document.getElementById('tag').innerText='{self.status.inner_text}';")
        if self.status.hor_align: 
            self.driver.execute_script(f"document.getElementById('tag').style['text-align']='center';")
        if self.status.ver_align:
            self.driver.execute_script(f"document.getElementById('tag').style['line-height']=document.getElementById('tag').style['height'];")

    # dynamic_css_prop를 대상으로 하여 저장된 데이터들을 메모리로 올림. 없다면 새로이 생성.
    # 파일 형식은 dict type
    def _load_data(self):
        temp_data_dict = dict()
        for dynamic_css_prop in self.dynamic_css_props.keys():
            file_path = os.path.join("data", dynamic_css_prop + ".txt")
            if not os.path.exists(file_path):
                os.mknod(file_path)
                temp_data_dict[dynamic_css_prop] = dict()
            else:
                with open(file_path, "r") as file:
                    contents = file.read()
                    if contents == "":
                        temp_data_dict[dynamic_css_prop] = dict()
                    else:
                        temp_data_dict[dynamic_css_prop] = eval(contents)
        return temp_data_dict
    
    # 새로 추가된 데이터를 포함하여 저장.
    def _save_data(self):
        dyn_css_props = list(self.dynamic_css_props.keys())
        for css_prop, data in self.total_data_dict.items():
            file_path = os.path.join("data", css_prop + ".txt")
            with open(file_path, "w") as file:
                file.write(str(data))

    # selenium을 활용하기 위하여 driver를 불러옴.
    def _get_driver(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--start-maximized")
        options.add_argument("window-size=2560,1440")
        driver = webdriver.Chrome(os.path.join(os.getcwd(), "chromedriver"), options=options)
        return driver
    
    # data가 있는지 확인하기 위한 함수
    ################# TODO######################################################################
    def _is_in_data(self, css_prop_val:dict()):
        for prop, val in css_prop_val.items():
            pass

    # dynamic_css_props에서 임의로 뽑은 값을 dict 형태로 반환.
    def _choice_temp_data(self):
        temp_css_data = dict()
        for css_prop, val in self.dynamic_css_props.items():
            if type(val) == tuple: # (min, max, interval)
                (min_v, max_v, interval) = val
                if "color" in css_prop:
                    red = random.choice([d for d in range(min_v, max_v, interval)])
                    green = random.choice([d for d in range(min_v, max_v, interval)])
                    blue = random.choice([d for d in range(min_v, max_v, interval)])
                    temp_css_data[css_prop] = f"rgb({red},{green},{blue})"
                else:
                    temp_css_data[css_prop] = f"{random.choice([d for d in range(min_v, max_v, interval)])}px"
            elif type(val) == list: # ["cate1", "cate2", ...]
                temp_css_data[css_prop] = random.choice(val)
        return temp_css_data

    # self.total_data_dict에 새로 생성한 값을 추가
    def _append_total_data_dict(self, image_name, temp_css_dict):
        for prop, val in temp_css_dict.items():
            self.total_data_dict[prop][image_name] = val
        

    # gen_count만큼 중복되지 않는 image 및 data를 생성.
    def tag_generator(self, gen_count):
        while gen_count != 0:
            if gen_count % 100 == 0:
                print(f"{self.gen_count - gen_count}/{self.gen_count}")

            
            temp_css_dict = self._choice_temp_data()
            image_name = f"img_{int(time.time()*1000)}.png"
            self._append_total_data_dict(image_name, temp_css_dict)
            self._capture_element(image_name, temp_css_dict)
            gen_count -= 1
    
    # selenium을 통해 css_dict에 맞게 적용된 이미지를 image_name으로 저장.
    def _capture_element(self, image_name, css_dict):
        image_path = os.path.join("images", image_name)

        _ = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        for prop, val in css_dict.items():
            self.driver.execute_script(f"document.getElementById('tag').style['{prop}']='{val}';")
        
        for prop, val in self.static_css_prop_val.items():
            self.driver.execute_script(f"document.getElementById('tag').style['{prop}']='{val}';")

        # status에 따라
        self._set_status()

        element = self.driver.find_element_by_css_selector("#tag")
        # get element location
        location = element.location 
        size = element.size
        left = location['x']
        top = location['y']
        
        # scroll down
        last_height = self.driver.execute_script(f"return document.documentElement.scrollHeight")
        if (last_height - top > 1440): # top에 맞출 수 있을 경우
            self.driver.execute_script(f"window.scrollTo(0, {top});")
            top = 0
        else:
            self.driver.execute_script(f"window.scrollTo(0, {last_height-1440})")
            top = top - (last_height-1440)

        right = left + size['width']
        bottom = top + size['height']

        # capture file
        img = self.driver.get_screenshot_as_png()
        img = Image.open(BytesIO(img))
        img = img.crop((int(left), int(top), int(right), int(bottom)))
        img.save(image_path)

    def run(self):
        self.driver.get(f"file://{os.path.join(os.getcwd(), 'test_html.html')}")
        self._set_status()
        self.tag_generator(self.gen_count)
        self._save_data()
        self.driver.quit()

if __name__ == '__main__':
    dynamic_css_props = {
                            "height":(100, 500, 4), 
                            "font-size":(13, 30, 1), 
                            "color":(0, 256, 1), 
                            "background-color":(0, 256, 1),
                            # "border-width":(1, 3, 1),
                            # "border-style":["solid", "dash"],
                            # "border-color":(0, 256, 1)
                        }
    static_css_prop_val = {
                            "background-color":"white"
                          }
    html_status = AutoGenStatus(ver_align=True, hor_align=False, inner_text="hello world!")
    autoTagGen = AutoTagGen(dynamic_css_props=dynamic_css_props, static_css_prop_val=static_css_prop_val, status=html_status, gen_count=1000)
    autoTagGen.run()