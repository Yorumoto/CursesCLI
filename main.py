import logging
import curses
import time
from random import randint
from enum import Enum
from curses import textpad
logging.basicConfig(filename="snek.log", filemode="w+", format="%(levelname)s -- %(message)s", level=logging.DEBUG)


class Frame:
    def __init__(self, src, y=0, x=0, height=20, width=40, filled=False, borderless=False):
        self.src = src
        self.x = x
        self.y = y
        self.height = height
        self.width = width
        self.borderless = borderless
        self.filled = filled
        self.addstr = []
        self.rendering_method = None

    def clear(self):
        self.addstr.clear()
        return self
    
    def set_rendering_method(self, new_method):
        self.rendering_method = new_method
        return self

    def render(self):
        if self.filled:
            h = self.height + self.borderless
            w = self.width + self.borderless

            for y in range(h):
                self.src.addstr(self.y + y, self.x, " " * w)

        if not self.borderless:
            textpad.rectangle(self.src, self.y, self.x, self.y + self.height, self.x + self.width)
        
        if self.rendering_method is not None:
            self.rendering_method(self, self.y, self.x)
            return self
        
        for index, item in enumerate(self.addstr):
            if not item:
                continue 
            # edit the coords

            # good question: how will you
            # get around this one with little boilerplate?
            #
            # ['sample text', curses.A_EFFECT] -> [0, 0, 'sample text', curses.A_EFFECT]
            # ['sample text'] -> [0, 0, 'sample text', curses.A_EFFECT]
           
            # scratch that
            # i'm not doing that

            if isinstance(item, list) and len(item) < 3:
                item.insert(0, 0)
                item.insert(0, index)
            elif isinstance(item, str):
                item = [index, 0, item]
            
            item[1] += self.x + 1
            item[0] += self.y + 1

            logging.debug(f'{index}: {item}')

            item[2] = item[2][0:self.width-2]
            self.src.addstr(*item)
    
        return self
    
    def abs_center(self, cy, cx):
        # logging.debug(f'{cy}, {cx}')
        return cy - (self.height // 2), cx - (self.width // 2)

    def append_items(self, *items):
        for x in items:
            self.addstr.append(x)
        # logging.debug(str(items))

        return self

class SnakeHead:
    def __init__(self, y, x):
        self.y = y
        self.x = x
        self.d = 0

class Food(SnakeHead):
    def __init__(self, snake):
        self.eaten = False

        area_height, area_width = snake.height - 1, snake.width - 1
        
        x = 0
        y = 0

        while True:
            x = randint(0, area_width)
            y = randint(0, area_height)
            
            con = False
            
            for body in snake.body:
                if body.x != x or body.y != y:
                    continue
                con = True
                break

            if con:
                continue
            else:
                break

        super().__init__(y, x)

class Snake:
    vectors = [
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1)
    ]
    
    opposite_vectors = [1,0,3,2]

    input_detects = {
        curses.KEY_LEFT : (0, 1),    
        curses.KEY_RIGHT : (1, 0),    
        curses.KEY_UP : (2, 3),    
        curses.KEY_DOWN : (3, 2),    
    }

    def __init__(self, y, x, width, height, game):
        self.ox = x
        self.oy = y
        self.game = game
        self.width = width
        self.height = height
        self.reset()
        self.move_timer = 0.25
        self.block = 0

    def mod_x(self, x):
        return x % self.width

    def mod_y(self, y):
        return y % self.height

    def update(self, inp):
        ax, ay = self.vectors[self.head.d]
        ox, oy, oh = self.head.x, self.head.y, self.head.d
        self.head.x = self.mod_x(self.head.x + ax)
        self.head.y = self.mod_y(self.head.y + ay)
        
        for body in self.body:
            if body == self.head:
                continue
            nox, noy, noh = body.x, body.y, body.d
            body.x, body.y, body.d = ox, oy, oh
            ox, oy, oh = nox, noy, noh

        bumped = False

        for body in self.body:
            if body == self.head:
                continue
            
            if self.head.x == body.x and self.head.y == body.y:
                self.game.game_over = True
                return
        
        for food in self.game.foods:
            if self.head.x != food.x or self.head.y != food.y:
                continue
            food.eaten = True
            self.game.score += 1
            self.grow()
            self.game.food_timer = 0

        if inp in self.input_detects:
            new_h, new_b = self.input_detects[inp]
           
            # logging.debug(f'new thing {new_h} {new_b}')
            if new_h != self.block:
                self.block = new_b
                self.head.d = new_h
    
    def grow(self):
        last = self.body[-1]
        ax, ay = self.vectors[self.opposite_vectors[last.d]]
        self.body.append(SnakeHead(self.mod_y(last.y + ay), self.mod_x(last.x + ax)))

    def reset(self):
        self.body = [SnakeHead(self.oy, self.ox+i) for i in range(6)]
        self.head = self.body[0]

def get_inp(src):
    return src.getch()

menu_frame = None
sel_ren = None

def select_items(src, prompt="", items=None, render=None):
    if render is None:
        logging.warning('select_items has been called with the absence of the "render" argument')

    if items is None:
        items = []

    index = 0
    inputted = True
    
    while True:
        if inputted:
            if render:
                render(prompt, [x[1] if len(x) > 1 else x[0] for x in items], index)
                            
            inputted = False
        
        inp = get_inp(src)
        if inp <= 0:
            return
        
        if inp == ord('\n'):
            return items[index][0]
        else:
            index = (index + (1 if inp == curses.KEY_DOWN else (-1 if inp == curses.KEY_UP else 0))) % len(items)
            inputted = True

def get_cen(src):
    # logging.debug(''.join(src.getmaxyx()))
    return [x//2 for x in list(src.getmaxyx())]

class Game:
    def __init__(self):
        self.foods = []
        self.reset()

    def reset(self):
        self.game_over = False
        self.food_timer = 0
        self.score = 0
        self.foods.clear()

def gamefunc(src):
    game = Game()
    
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_RED)
    food_color = curses.color_pair(2)

    def game_render(self, y, x):
        self.src.addstr(y-2, x, f"Score: {game.score}") 

        for point in snake.body:
            # logging.debug(f'{point.x}, {point.y}')
            self.src.addstr(y+point.y+1, x+point.x+1, ' ', curses.A_REVERSE)
        
        for food in game.foods:
            self.src.addstr(y+food.y+1, x+food.x+1, ' ', food_color)

    game_frame = Frame(src, width=80, height=30).set_rendering_method(game_render)
    snake = Snake(y=game_frame.height//2, x=game_frame.width//2, width=game_frame.width-1, height=game_frame.height-1, game=game)
    src.nodelay(True)
    # last_time = time.time()

    def reset_game():
        global score, food_timer, foods
        snake.reset()
        game.reset()
        src.nodelay(True)
        
        # flushed
        

    reset_game()
    

    while True:
        # current_time = time.time()
        # delta_time = current_time - last_time
        # last_time = current_time
        
        # polling
        
        if game.game_over:
            src.nodelay(False)
            
            sel = select_items(src, f"Game Over | Score: {game.score}", [[1, 'Restart'], [2, 'Back to Menu']], render=sel_ren)
            
            if sel == 1:
                reset_game()
                continue
            elif sel == 2:
                break

        inp = get_inp(src)
        
        if inp == ord('p'):
            src.nodelay(False)
            sel = select_items(src, "Game Paused", [[0, 'Resume'], [1, 'Restart'], [2, 'Back to Menu']], render=sel_ren)
            
            if sel == 1:
                reset_game()
                continue
            elif sel == 2:
                break

            src.nodelay(True)
        
        # update
        game.food_timer -= 1

        if game.food_timer <= 0:
            game.foods.append(Food(snake))
            game.food_timer = randint(5, 90)
        
        game.foods = [x for x in game.foods if not x.eaten]

        snake.update(inp)
        # render
        src.clear()

        try:
            game_frame.y, game_frame.x = game_frame.abs_center(*get_cen(src))
            game_frame.render()
            # src.addstr('cmon')
        except curses.error:
            src.addstr("Game Rendering cannot fit in this terminal")

        src.refresh()
        time.sleep(0.1)

def menu(src): 
    select_items(src, "Snake", [[gamefunc, 'Play'], [lambda _: exit(0), 'Exit']], render=sel_ren)(src)

def main(src):
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    color_pair = curses.color_pair(1)

    menu_frame = Frame(src, filled=True, width=40, height=10)
    
    global sel_ren 
    def sel_ren(prompt, str_items, highlighted):
        src.clear()
        try:
            src.attron(color_pair)
            menu_frame.y, menu_frame.x = menu_frame.abs_center(*get_cen(src))
            # logging.warning(f'{frame.x}, {frame.y}')
            menu_frame.clear().append_items((((menu_frame.width // 2) - (len(prompt) // 2)) * " ") + prompt, "", *[(">> " if i==highlighted else "   ")+ x for i, x in enumerate(str_items)])
            menu_frame.render()

            src.attroff(color_pair)
        except curses.error:
            src.addstr('Game Rendering cannot fit in this terminal')    
        src.refresh()
    
    logging.debug('Hello!')
    # src.nodelay(True)
    src.clear()
    
    while True:
        menu(src)

src = curses.initscr()
curses.noecho()
curses.curs_set(0)
curses.wrapper(main)
