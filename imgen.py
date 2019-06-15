
import os
from enum import IntEnum
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
from data import Rooster, init_db, db_session

class Side(IntEnum):
    LEFT, RIGHT = range(2)

class BarText(IntEnum):
    NO_TEXT, FACTOR, CURRENT_TOTAL = range(3)

class HitType(IntEnum):
    NO_HIT, HIT, CRITICAL = range(3)

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

def uvfilter(img, flt):
    # resize to save calculations on image iteration
    flt = flt.resize(img.size, Image.ANTIALIAS)
    src = img.copy()
    srcd = src.load()
    imgd = img.load()
    uvd = flt.load()
    for x in range(src.width):
        for y in range(src.height):
            new = uvd[x, y]
            imgd[x, y] = srcd[new[0]*src.width/256, new[1]*src.height/256]
    return img

def distort_sprite(sprite, mask=os.path.join(ASSETS_ROOT, 'ui/distort_mask.png')):
    return uvfilter(Image.open(os.path.join(ROOSTERS_ROOT, sprite)).convert('RGBA'), Image.open(mask))

def create_progressbar(current, total=1, prev=None, mode=BarText.FACTOR, width=BAR_WIDTH, anchor=Side.LEFT, bg_color='#000000', fg_color='#FF000050', prev_color="#FF0000"):
    prev = current if prev is None else prev
    prev_factor = prev / total
    factor = current / total
    MARGIN = BAR_MARGIN
    bg_size = width, 30
    bg = Image.new('RGB', bg_size, color=bg_color)

    BAR_PREV = 0
    for i, f in enumerate((prev_factor, factor)):
        fg_width = round(bg_size[0]*f)
        if fg_width > 0:
            fg_size = max(1, fg_width-MARGIN*2), bg_size[1]-MARGIN*2
            color = prev_color if i == BAR_PREV else fg_color
            fg = Image.new('RGBA', fg_size, color=color)
            x_pos = MARGIN if anchor == Side.LEFT else width-fg_width+MARGIN
            bg.paste(fg, (x_pos, MARGIN), fg)

    if mode != BarText.NO_TEXT:
        d = ImageDraw.Draw(bg)
        if mode == BarText.FACTOR:
            txt = "%d%%" % (factor*100)
        elif mode == BarText.CURRENT_TOTAL:
            txt = "%d/%d" % (current, total)
        fnt = font(REGULAR_FONT, 12)
        txt_size = d.textsize(txt, font=fnt)
        txt_x = MARGIN*2 if anchor == Side.LEFT else width-txt_size[0]-MARGIN*2
        d.text((txt_x, MARGIN), txt, fill='white', font=fnt)
    return bg

def create_progressbar2(current, total=1, prev=None, mode=BarText.FACTOR, anchor=Side.LEFT, fg_color='#FF000050', prev_color="#FF0000"):
    return create_progressbar(current, total, prev, mode, BAR_WIDTH, anchor, '#000000', fg_color, prev_color)

def create_hpbar(current, total=1, prev=None, mode=BarText.NO_TEXT, anchor=Side.LEFT):
    # Helper function for HP
    return create_progressbar2(current, total, prev, mode, anchor, '#FFFF00', '#FF0000')

def create_apbar(current, total=1, prev=None, mode=BarText.CURRENT_TOTAL, anchor=Side.LEFT):
    # Helper function for AP
    return create_progressbar2(current, total, prev, mode, anchor, '#0000FF', '#0000FF50')

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

def create_battlebg(lalign=270):
    bg = Image.open(os.path.join(ASSETS_ROOT, 'ui/ui_background.png'))
    gr = Image.open(os.path.join(ASSETS_ROOT, 'ui/ui_ground.png')).convert('RGBA')
    ralign = bg.width - lalign
    align = lalign, ralign
    for a in align:
        bg.paste(gr, (a-gr.width//2, 400), gr)
    return bg

def create_battle(a:Rooster, b:Rooster, mirror=Side.RIGHT, hit=None, hit_type=HitType.NO_HIT, highlight=None):
    X, Y, W, H = range(4)
    lalign = 270
    bg = create_battlebg()
    ralign = bg.width - lalign
    align = lalign, ralign

    rt_rect_size = 275, 275
    rt_rect_y = 175
    rt_rect = {
        Side.LEFT: (align[Side.LEFT]-rt_rect_size[X]//2, rt_rect_y, *rt_rect_size),
        Side.RIGHT: (align[Side.RIGHT]-rt_rect_size[X]//2, rt_rect_y, *rt_rect_size),
    }
    rts = {
        Side.LEFT: a,
        Side.RIGHT: b,
    }
    hp_y = 72
    ap_y = 110
    hit_x = -60
    hit_y = 80
    for r in rts.keys():
        rt = rts[r]
        # Rooster sprite
        im = Image.open(os.path.join(ROOSTERS_ROOT, rt.sprite)).convert('RGBA')
        if r == mirror:
            im = ImageOps.mirror(im)
        rect = rt_rect[r]
        im.thumbnail(rt_rect[r][2:])
        mask = im.copy()
        if hit == rt:
            im = im.filter(ImageFilter.BLUR)
        if highlight != None and highlight != rt:
            im = ImageOps.grayscale(im)
        pos = rect[X] + (rect[W] - im.width)//2, rect[Y] + rect[H] - im.height
        bg.paste(im, pos, mask)
        # Hitspark
        if hit == rt:
            hit_im = None
            if hit_type == HitType.HIT:
                hit_im = Image.open(os.path.join(ASSETS_ROOT, 'ui/ui_hitspark.png')).convert('RGBA')
            elif hit_type == HitType.CRITICAL:
                hit_im = Image.open(os.path.join(ASSETS_ROOT, 'ui/ui_hitspark_critical.png')).convert('RGBA')
            if r == Side.LEFT:
                bg.paste(hit_im,(align[Side.LEFT]+hit_x, hit_y) , hit_im)
            else:
                bg.paste(hit_im,(align[Side.RIGHT]-hit_im.width-hit_x, hit_y) , hit_im)
        # Rooster name
        d = ImageDraw.Draw(bg)
        name_fnt = font(BOLD_FONT, 30)
        name_size = d.textsize(rt.name, font=name_fnt)
        pos = align[r]-name_size[X]//2, 0
        fill = '#00000050' if highlight != None and highlight != rt else '#000000'
        d.text(pos, rt.name, font=name_fnt, fill=fill)
        # HP and AP
        anchor = Side.LEFT if r == Side.RIGHT else Side.RIGHT
        hp_x = align[r]-BAR_WIDTH//2
        hp = create_hpbar(rt.hp, rt.HP, rt.hp_prev, anchor=anchor)
        if highlight != None and highlight != rt:
            hp = ImageOps.grayscale(hp)
        bg.paste(hp, (hp_x, hp_y))
        if 1:
            ap = create_apbar(rt.ap, rt.AP, rt.ap_prev, anchor=anchor)
            if highlight != None and highlight != rt:
                ap = ImageOps.grayscale(ap)
            bg.paste(ap, (hp_x, ap_y))
    return bg

def create_highlight(a:Rooster, b:Rooster, highlight=None):
    return create_battle(a, b, highlight=highlight)

if __name__ == '__main__':
    from cmd import Cmd
    import tk

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
            tk.show_img(create_movebar(text, ap))

        def do_hp(self, args):
            """Generate HP bar.\n\tUsage: hp [value=0..100] [anchor=left|right]
            """
            import random
            args = args.strip().split(' ')
            anchors = {
                'left': Side.LEFT, 'right': Side.RIGHT
            }
            anchor = random.choice(list(anchors.values()))
            if len(args) > 1:
                print(args)
                anc = anchors.get(args[1])
                anchor = anc if anc != None else anchor
            if args[0] == '':
                value = random.random()
            else:
                value = int(args[0].replace('%', ''))/100
            tk.show_img(create_hpbar(value, prev=min(value+0.1, 1), anchor=anchor))

        @db_session
        def do_battle(self, args):
            """Generate battle image (needs db session).\n\tUsage: battle [sprite-a] [sprite-b]
            """
            from random import choice
            args = args.strip().split(' ')
            a, b = Rooster.select().random(2)
            if args[0] != '':
                a = Rooster.get(sprite=args[0])
                if len(args) > 1:
                    b = Rooster.get(sprite=args[1])
            a.reset()
            b.reset()
            tk.show_img(create_battle(a, b, hit=choice([a, b]), hit_type=choice([HitType.HIT, HitType.CRITICAL])))

        @db_session
        def do_start(self, args):
            """Generate start (presentation) image (needs db session).\n\tUsage: start [sprite-a] [sprite-b]
            """
            from random import choice
            args = args.strip().split(' ')
            a, b = Rooster.select().random(2)
            if args[0] != '':
                a = Rooster.get(sprite=args[0])
                if len(args) > 1:
                    b = Rooster.get(sprite=args[1])
            a.reset()
            b.reset()
            tk.show_img(create_highlight(a, b, choice([a, b])))
        
        @db_session
        def do_distort(self, args):
            """Distort sprite using the default mask.\n\tUsage: distort [sprite]
            """
            sprite = ''
            args = args.strip().split(' ')
            if args[0] != '':
                sprite = args[0]
            else:
                sprite = Rooster.select().random(1)[0].sprite
            tk.show_img(distort_sprite(sprite))

    init_db()
    tk.init_tk()
    ImagePreviewCmd().cmdloop()
