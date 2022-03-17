import logging
import curses
import random
from curses import textpad
logging.basicConfig(filename="d.log", filemode="w+", format="%(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)

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
    
    def append_items(self, *items):
        for x in items:
            self.addstr.append(x)

        return self

def main(src):
    # frame = Frame(src).append_items(['hello'], ['this is a certified'], ['TERMINAL MOMENT', curses.A_REVERSE], [5, 0, ''.join([chr(random.randint(32, 128)) for i in range(1, 1001)])])
    # overlap_frame = Frame(src, 5, 5, 10, 20).append_items(['get overlapped lol'])
   
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_RED)
    inside_pair = curses.color_pair(2)

    def ren(self, y, x):
        src.attron(inside_pair)
        Frame(src=src, x=x+3, y=y+2, width=8, height=4, filled=True).render()
        src.attroff(inside_pair)

    func_frame = Frame(src, x=5, y=10, width=25, height=10).set_rendering_method(ren)
    
    # code smell?
    data = {
        'John Doe': {
            'age': 23,
            'job': 'Butler',
            'height': 1.8,
            'graduated': False
        },
        
        'Jane Doe': {
            'age': 30,
            'job': 'Lawyer',
            'height': 1.65,
            'graduated': True
        },

        'John Smith': {
            'age': 55,
            'job': 'Farmer',
            'height': 1.7,
            'graduated': True
        }
    }


    src.clear()
   
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
    this_pair = curses.color_pair(1)

    for index, (name, data) in enumerate(data.items()):
        src.attron(this_pair)
        Frame(src, x=index*25, y=0, width=23, height=6, borderless=True, filled=True).append_items(
            [name, curses.A_REVERSE], 
            '', 
            f"Age: {data['age']}", 
            f"Occupation: {data['job']}", 
            f'Height: {data["height"]}m'
        ).render()
        src.attroff(this_pair)

    func_frame.render()
    src.refresh()
    src.getch()

try:
    curses.wrapper(main)
except KeyboardInterrupt:
    pass
