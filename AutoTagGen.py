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


class AutoTagGen:
    """
        테스트 데이터를 생성하기 위해 비교적 단순한 태그들을 캡쳐해주는 클래스
        data에 관한 정보는 data/total_data.txt 에 저장된다.
        capture 된 이미지는 images/ 폴더 안에 저장된다.

        (기능) 특정 css prop를 고정하고, 그 외의 css prop를 변경(random.choice)하여 저장
        (제한 사항) 저장형식은 2d array 형식이고, 맨 위에는 해당 column의 데이터가 저장되게 된다.       
    """
    def __init__(self, static_css_prop_val:dict(), inner_text:str=None):
        self.driver = self._get_driver()
        self.static_css_prop_val = static_css_prop_val                                              # 고정해야 하는 css prop
        self.dynamic_css_props = ["image_name", "height", "font-size", "color", "background-color"] # 동적으로 변경될 css prop
        self.inner_text = inner_text                                                                # tag 내의 word 변경 default로는 "test text"
        self.total_data_path = "data/total_data.txt"                                                # total_data.txt가 저장될 경로
        if not os.path.exists(self.total_data_path):                                                # 모든 데이터를 저장할 total_data.csv 파일 생성
            os.mknod(self.total_data_path)
            self.total_data = list()
        else:
            self.total_data = self._get_total_data()

    # 새로 생성한 데이터를 포함하여 total_data.txt에 저장한다.
    def _save_total_data(self):
        self.total_data.insert(0, self.dynamic_css_props)
        with open(self.total_data_path, "w") as file:
            for data in self.total_data:
                data = "||".join(list(map(str, data))) 
                file.write(data + "\n")
    
    # 기존에 저장되어 있던 total_data를 불러온다.  
    def _get_total_data(self):
        total_data = None
        with open(self.total_data_path, "r") as file:
            total_data = file.read()
        total_data = [data for data in total_data.split("\n") if data.strip() != ""][1:] # except first row
        total_data = [data.split("||") for data in total_data]
        return total_data

    # selenium을 활용하기 위하여 driver를 불러옴.
    def _get_driver(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--start-maximized")
        options.add_argument("window-size=2560,1440")
        driver = webdriver.Chrome("chromedriver", options=options)
        return driver
    
    # gen_count만큼 중복되지 않는 image 및 data를 생성.
    def tag_generator(self, gen_count):
        def _is_in_data(height, font_size, color, bg_color):       # data가 이미 total_data에 있는지 확인하기 위한 함수
            for data in self.total_data:
                (_, h, f_s, c, bg_c) = data
                if h == height and f_s == font_size and c == color and bg_c == bg_color:
                    return True
            return False

        # 뽑을 수 있는 값의 제한선
        height_vals = [h for h in range(100, 500, 5)]
        font_size_vals = [f for f in range(13, 30, 1)]
        color_vals = [c for c in range(0, 256, 1)]
        
        while gen_count != 0:
            # random하게 값을 뽑음.
            height = random.choice(height_vals)
            font_size = random.choice(font_size_vals)
            color = (random.choice(color_vals), random.choice(color_vals), random.choice(color_vals))
            bg_color = (random.choice(color_vals), random.choice(color_vals), random.choice(color_vals))

            # total_data에 없을 때만 추가
            if not _is_in_data(height, font_size, color, bg_color):
                image_name = f"image_{int(time.time()*1000)}.png"
                temp_dict = dict()
                self.total_data.append([image_name, f"{height}px", f"{font_size}px", f"rgb{color}", f"rgb{bg_color}"])
                temp_dict["height"] = f"{height}px"
                temp_dict["font-size"] = f"{font_size}px"
                temp_dict["color"] = f"rgb{color}"
                temp_dict["background-color"] = f"rgb{bg_color}"
                self._capture_element(image_name, temp_dict)
            gen_count -= 1
    
    # selenium을 통해 css_dict에 맞게 적용된 이미지를 image_name으로 저장.
    def _capture_element(self, image_name, css_dict):
        image_path = os.path.join("images", image_name)

        _ = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        for prop, val in css_dict.items():
            self.driver.execute_script(f"document.getElementById('tag').style['{prop}']='{val}';")
        
        for prop, val in self.static_css_prop_val.items():
            self.driver.execute_script(f"document.getElementById('tag').style['{prop}']='{val}';")

        element = self.driver.find_element_by_css_selector("#tag")
        if self.inner_text:
            self.driver.execute_script(f"document.getElementById('tag').innerText='{self.inner_text}';")
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
        self.tag_generator(5)
        self._save_total_data()

if __name__ == '__main__':
    css_prop_val = {"text-align":"left"}
    autoTagGen = AutoTagGen(css_prop_val, inner_text="Hello world!!")
    autoTagGen.run()