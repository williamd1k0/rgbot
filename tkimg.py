
# Some envs don't have Python configured for Tk, such as Heroku.
_TK_SUPPORT = True
try:
    from tkinter import Tk, Label
    from PIL import ImageTk
except ModuleNotFoundError:
    _TK_SUPPORT = False

ROOT = None
IMG = None
PANEL = None

def init_tk():
    if not _TK_SUPPORT: return
    global ROOT, PANEL
    ROOT = Tk()
    ROOT.title('Rinha de Galo BOT [Tk]')
    PANEL = Label(ROOT)

def show_img(img):
    if not _TK_SUPPORT: return
    global IMG, PANEL
    IMG = ImageTk.PhotoImage(img)
    PANEL.configure(image=IMG)
    PANEL.pack(side="bottom", fill="both", expand="yes")

