from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException

import requests
import re

from offset_moves import get_offset_5x5, get_offset_9x9, get_offset_19x19
from action_space import action_map_5x5, reverse_action_map_5x5, action_map_9x9, reverse_action_map_9x9, action_map_19x19, reverse_action_map_19x19
from private import PASSWORD_PRODUCTION, PASSWORD_LOCALHOST

URL_PRODUCTION = 'https://govariants.com/'
URL_LOCALHOST = 'http://localhost:5173/'

VARIANT = 'quantum'
WIDTH = 5
HEIGHT = 5

USERNAME_PRODUCTION = 'QuantumBot'
PASSWORD_PRODUCTION = PASSWORD_PRODUCTION

USERNAME_LOCALHOST = 'QuantumBotTest'
PASSWORD_LOCALHOST = PASSWORD_LOCALHOST

class Board:

    def __init__(self):
        
        self.game_id = None

        self.stone_coordinates = []
        
        options = webdriver.ChromeOptions()
        #options.add_argument("--headless")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        self.driver.set_window_position(1000, 0)
        self.driver.set_window_size(900, 900)
    
    def get_driver(self):
        return self.driver
    
    def login(self):

        self.driver.get(URL_LOCALHOST + "login")
        self.driver.implicitly_wait(10)  # Wait for the page to load completely

        print("At login page Current URL:", self.driver.current_url)

        username_input = self.driver.find_element(By.XPATH, '//input[@id="username"]')
        username_input.clear()
        username_input.send_keys(USERNAME_LOCALHOST)

        password_input = self.driver.find_element(By.XPATH, '//input[@id="current-password"]')
        password_input.clear()
        password_input.send_keys(PASSWORD_LOCALHOST)

        login_button = self.driver.find_element(By.XPATH, '//button[@type="submit" and contains(text(), "Log in")]')
        login_button.click()

        WebDriverWait(self.driver, 20).until(EC.url_to_be(URL_LOCALHOST))

        print("Logged in. Current URL:", self.driver.current_url)

    def create_game(self):

        variant_select = Select(self.driver.find_element(By.XPATH, '//div[@class="game-creation-form"]//select'))
        variant_select.select_by_visible_text(VARIANT)

        width_input = self.driver.find_element(By.XPATH, '//form[@class="config-form-column"]//label[text()="Width"]/following-sibling::input[@type="number"]')
        width_input.clear()
        width_input.send_keys(WIDTH)

        height_input = self.driver.find_element(By.XPATH, '//form[@class="config-form-column"]//label[text()="Height"]/following-sibling::input[@type="number"]')
        height_input.clear()
        height_input.send_keys(HEIGHT)

        create_game_button = self.driver.find_element(By.XPATH, '//div[@class="game-creation-form"]//button[text()="Create Game"]')
        create_game_button.click()

        WebDriverWait(self.driver, 20).until(EC.url_contains('/game/'))

        self.game_id = self.driver.current_url.split('/')[-1]

        print("Game created. Current URL:", self.driver.current_url)

    def get_sgf_data(self):

        response = requests.get(URL_LOCALHOST + "api/game/" + self.game_id + "/sgf")
        if response.status_code == 200:
            sgf_data = re.findall(r';[BW]\[[a-z]{2}\]',response.content.decode('utf-8'))
            processed_actions = []
            for move in sgf_data:
                #converts letter coordinates to numerical coordinates then gets the key corrresponding to the numerical coordinates and adds it to processed_actions list
                processed_actions.append(reverse_action_map_5x5.get(tuple([ord(move[3:-1][0])-ord('a')+1, ord(move[3:-1][1])-ord('a')+1]), 'invalid'))
            return processed_actions
        else: 
            print("Error getting game moves")

    # use get_sgf_data instead b/c this function does not account for the case that the both quantum boards may be in different states
    def board_state(self):

        normal_stone_coordinates = []
        quantum_stone_coordinates = []
        
        #obtains the coordinates of the normal stones on the board
        circles = self.driver.find_elements(By.CSS_SELECTOR, 'circle')

        #obtains the coordinates of the quantum stones on the board
        all_g_elements = WebDriverWait(self.driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'g'))
        )
        quantum_stones = [g for g in all_g_elements if g.get_attribute('transform') and 'translate' in g.get_attribute('transform')]

        #addes one to the coordinates because the board is 0 indexed
        for circle in circles:
            cx = int(circle.get_attribute('cx'))+1
            cy = int(circle.get_attribute('cy'))+1
            normal_stone_coordinates.append([cx, cy])
        
        for stone in quantum_stones:
            transform_attr = stone.get_attribute('transform')

            # removes the translate() string and adds one to the coordinates because the board is 0 indexed
            quantum_stone_coordinates.append([int(coordinate) + 1 for coordinate in re.split(" ", transform_attr.replace('translate(', '').replace(')', ''))])

        stone_coordinates = quantum_stone_coordinates[:len(quantum_stone_coordinates) // 2] + normal_stone_coordinates[:len(normal_stone_coordinates) // 2]
        return stone_coordinates

    def get_game_result(self):
        
        #checks if the game has ended or not. if true the result is returned, if false, False is returned
        try:
        # Attempts to find the result element
            result = self.driver.find_element(By.XPATH, '//div[contains(text(), "Result:")]')
            return (result.text.removeprefix("Result: "))[0]
        
        except NoSuchElementException as e:
            return False
    
    def __del__(self):
        self.driver.quit()

class Player:

    def __init__(self, color, board_driver):

        self.color = color
        self.driver = board_driver

    def get_color(self):
        return self.color

    def take_seat(self):
        take_seat_button = self.driver.find_element(By.XPATH, '//div[@class="timer-and-button"]//button[text()="Take Seat"]')
        take_seat_button.click()

    def make_move(self, action):
        if action == 25:
            #press pass button
            pass_button = self.driver.find_element(By.XPATH, '//button[contains(text(), "Pass")]')
            pass_button.click()
        elif action == 26:
            #press resign button
            resign_button = self.driver.find_element(By.XPATH, '//button[contains(text(), "Resign")]')
            resign_button.click()
        else:
            board_svg = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'svg.board'))
            )
            # we need the offset because it corresponds an action to a specific spot on the board for the driver to click on 
            offset_x, offset_y = get_offset_5x5(action_map_5x5[action])
            action_chains = ActionChains(self.driver)
            action_chains.move_to_element_with_offset(board_svg, offset_x, offset_y).click().perform()

    def select_player(self, player_has_passed=False):

        if(player_has_passed):
            select_player_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.seat'))
            )
            select_player_button.click()
        else:
            select_player_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.seat.to-move'))
            )
            select_player_button.click()
    
    def __del__(self):
        self.driver.quit()
        
