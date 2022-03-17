import curses
from curses import textpad

class InputManager:
    def __init__(self, src):
        self.src = src

    def get_input(self):
        try:
            return self.src.getch()
        except curses.error:
            pass

class Textbar:
    def __init__(self, src):
        self.src = src
        self.textbox = textpad.Textbox(src)
        self.editing = False
    
    def edit(self, setv):
        if not self.editing and setv == True:
            text = self.textbox.edit()
            self.src.addstr(0, 0, text)
        elif self.editing and setv == False:
            self.textbox.do_command(chr(7))
        self.editing = not setv

    def render(self):
        y, _ = self.src.getmaxyx()
        
        try:
            self.src.addstr(y-1, 0, self.textbox.gather())
        except curses.error:
            pass

def main(src):
    src.clear()
    src.nodelay(True)

    input_manager = InputManager(src)
    textbar = Textbar(src)

    while True:
        inp = input_manager.get_input()
        
        if inp == ord(":"):
            textbar.edit(True)
        elif inp == ord('\n'):
            textbar.edit(False)

        textbar.render() 
        src.refresh()    

try:
    curses.wrapper(main)
except KeyboardInterrupt:
    pass
