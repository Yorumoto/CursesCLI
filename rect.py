import curses
from curses import textpad

def filled_rect(src, sx, sy, ex, ey):
    pass

def main(src):
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
    
    textpad.rectangle(src, 5, 5, 10, 25)
    src.attron(curses.color_pair(1))
    # textpad.rectangle(src, 20, 5, 30, 30)
    filled_rect(src, 20, 5, 30, 30)
    src.refresh()
    src.getch()

curses.wrapper(main)
