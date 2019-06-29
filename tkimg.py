
from tkinter import Tk, Label
from PIL import ImageTk

ROOT = None
IMG = None
PANEL = None

def init_tk():
    global ROOT, PANEL
    ROOT = Tk()
    ROOT.title('Rinha de Galo BOT [Tk]')
    PANEL = Label(ROOT)

def show_img(img):
    global IMG, PANEL
    IMG = ImageTk.PhotoImage(img)
    PANEL.configure(image=IMG)
    PANEL.pack(side="bottom", fill="both", expand="yes")

