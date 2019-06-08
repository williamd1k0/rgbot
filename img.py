
import os
from PIL import Image, ImageDraw, ImageFont, ImageOps
from data import Rooster, init_db, db_session

LEFT = 0
RIGHT = 1
BAR_MARGIN = 3
BAR_WIDTH = 275
ASSETS_ROOT = 'data/assets/'
ROOSTERS_ROOT = os.path.join(ASSETS_ROOT, 'roosters')
REGULAR_FONT = os.path.join(ASSETS_ROOT, 'ui/OpenDyslexic3-Regular.ttf')
BOLD_FONT = os.path.join(ASSETS_ROOT, 'ui/OpenDyslexic3-Bold.ttf')
FONT_CACHE = {}


def font(path, size):
    if not path in FONT_CACHE:
        FONT_CACHE[path] = {}
    if not size in FONT_CACHE[path]:
        FONT_CACHE[path][size] = ImageFont.truetype(path, size)
    return FONT_CACHE[path][size]


def create_hpbar(factor, width=BAR_WIDTH, anchor=LEFT, bg_color='#000000', fg_color='#FF0000'):
    MARGIN = BAR_MARGIN
    bg_size = width, 30
    bg = Image.new('RGB', bg_size, color=bg_color)

    fg_width = round(bg_size[0]*factor)
    if fg_width > 0:
        fg_size = fg_width-MARGIN*2, bg_size[1]-MARGIN*2
        fg = Image.new('RGB', fg_size, color=fg_color)
        x_pos = MARGIN if anchor == LEFT else width-fg_width+MARGIN
        bg.paste(fg, (x_pos, MARGIN))

    if 1:
        d = ImageDraw.Draw(bg)
        txt = "%d%%" % (factor*100)
        txt_size = d.textsize(txt)
        txt_x = MARGIN*2 if anchor == LEFT else width-txt_size[0]-MARGIN*2
        d.text((txt_x, MARGIN*2), txt, fill='white')
    return bg

def create_movebar(text, ap=0, color='#000000', path='data/assets/ui/ui_button.png'):
    bar = Image.open(path)
    d = ImageDraw.Draw(bar)
    
    name_fnt = font(REGULAR_FONT, 42)
    name_size = d.textsize(text, font=name_fnt)
    d.text(((bar.width-name_size[0])//2, (bar.height-name_size[1])//8), text, font=name_fnt, fill=color)
    
    ap_fnt = font(BOLD_FONT, 42)
    ap_txt = 'AP%02d' % ap
    ap_size = d.textsize(ap_txt, font=ap_fnt)
    d.text((bar.width-ap_size[0]-10, bar.height-ap_size[1]-10), ap_txt, font=ap_fnt, fill=color)
    return bar

def create_battle(a:Rooster, b:Rooster, mirror=RIGHT):
    X, Y, W, H = range(4)
    bg = Image.open('data/assets/ui/ui_background.png')
    gr = Image.open('data/assets/ui/ui_ground.png').convert('RGBA')
    lcenter = 270
    rcenter = bg.width - lcenter
    centers = lcenter, rcenter
    for c in centers:
        bg.paste(gr, (c-gr.width//2, 400), gr)

    rt_rect_size = 275, 275
    rt_rect_y = 175
    rt_rect = {
        LEFT: (centers[LEFT]-rt_rect_size[X]//2, rt_rect_y, *rt_rect_size),
        RIGHT: (centers[RIGHT]-rt_rect_size[X]//2, rt_rect_y, *rt_rect_size),
    }
    rts = {
        LEFT: a,
        RIGHT: b,
    }
    hp_y = 72
    ap_y = 110
    hp_w = BAR_WIDTH
    for r in rts.keys():
        rt = rts[r]
        # Rooster sprite
        im = Image.open(os.path.join(ROOSTERS_ROOT, rt.sprite)).convert('RGBA')
        if r == mirror:
            im = ImageOps.mirror(im)
        rect = rt_rect[r]
        im.thumbnail(rt_rect[r][2:])
        pos = rect[X] + (rect[W] - im.width)//2, rect[Y] + rect[H] - im.height
        bg.paste(im, pos, im)
        # Rooster name
        d = ImageDraw.Draw(bg)
        name_fnt = font(BOLD_FONT, 30)
        name_size = d.textsize(rt.name, font=name_fnt)
        pos = centers[r]-name_size[X]//2, 0
        d.text(pos, rt.name, font=name_fnt, fill='#000000')
        # HP and AP
        anchor = LEFT if r == RIGHT else RIGHT
        hp_x = centers[r]-hp_w//2
        hp = create_hpbar(rt.hp/rt.HP, width=hp_w, anchor=anchor)
        bg.paste(hp, (hp_x, hp_y))
        if 1:
            ap = create_hpbar(rt.ap/rt.AP, width=hp_w, anchor=anchor, fg_color='#0000FF')
            bg.paste(ap, (hp_x, ap_y))
    return bg


if __name__ == '__main__':
    from cmd import Cmd

    class ImagePreviewCmd(Cmd):
        prompt = 'gen> '
        intro = "Image generation preview. Type help/? to list commands"

        def do_exit(self, inp):
            """Exit prompt.
            """
            return True
        do_EOF = do_exit

        def do_moves(self, args):
            """Generate Move UI button.\n\tUsage: moves [ap] attack-name
            """
            args = args.split(' ')
            has_ap = False
            try:
                ap = int(args[0])
                has_ap = True
            except:
                import random
                ap = random.randint(0, 30)
            text = ' '.join(args[1 if has_ap else 0:])
            create_movebar(text, ap).show()

        def do_hp(self, args):
            """Generate HP bar.\n\tUsage: hp [value=0..100] [anchor=left|right]
            """
            import random
            args = args.strip().split(' ')
            anchors = {
                'left': LEFT, 'right': RIGHT
            }
            anchor = random.choice(list(anchors.values()))
            if len(args) > 1:
                anchor = anchors.get(args[1]) or anchor
            if args[0] == '':
                value = random.random()
            else:
                value = int(args[0].replace('%', ''))/100
            create_hpbar(value, anchor=anchor).show()

        @db_session
        def do_battle(self, args):
            """Generate battle image (needs db session).\n\tUsage: battle [sprite-a] [sprite-b]
            """
            args = args.strip().split(' ')
            a = Rooster.select().random(1)[0]
            b = Rooster.select().random(1)[0]
            if args[0] != '':
                a = Rooster.get(sprite=args[0])
                if len(args) > 1:
                    b = Rooster.get(sprite=args[1])
            a.reset()
            b.reset()
            create_battle(a, b).show()

    init_db()
    ImagePreviewCmd().cmdloop()
