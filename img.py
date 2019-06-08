
import os
from PIL import Image, ImageDraw, ImageFont, ImageOps

LEFT = 0
RIGHT = 1
BAR_MARGIN = 3
BAR_WIDTH = 180
ASSETS_ROOT = 'data/assets/'
ROOSTERS_ROOT = os.path.join(ASSETS_ROOT, 'roosters')
REGULAR_FONT = os.path.join(ASSETS_ROOT, 'ui/OpenDyslexic3-Regular.ttf')
BOLD_FONT = os.path.join(ASSETS_ROOT, 'ui/OpenDyslexic3-Bold.ttf')

FONT_CACHE = {
    REGULAR_FONT: {
        42: ImageFont.truetype(REGULAR_FONT, 42),
    },
    BOLD_FONT: {
        42: ImageFont.truetype(BOLD_FONT, 42)
    }
}

def create_hpbar(factor, width=BAR_WIDTH, anchor=LEFT, bg_color='#000000', fg_color='#FF0000'):
    MARGIN = BAR_MARGIN
    bg_size = width, 30
    fg_width = round(bg_size[0]*factor)
    fg_size = fg_width-MARGIN*2, bg_size[1]-MARGIN*2

    bg = Image.new('RGB', bg_size, color=bg_color)
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
    
    name_fnt = FONT_CACHE[REGULAR_FONT][42]
    name_size = d.textsize(text, font=name_fnt)
    d.text(((bar.width-name_size[0])//2, (bar.height-name_size[1])//8), text, font=name_fnt, fill=color)
    
    ap_fnt = FONT_CACHE[BOLD_FONT][42]
    ap_txt = 'AP%02d' % ap
    ap_size = d.textsize(ap_txt, font=ap_fnt)
    d.text((bar.width-ap_size[0]-10, bar.height-ap_size[1]-10), ap_txt, font=ap_fnt, fill=color)
    return bar

def create_battle(a, b, mirror=RIGHT):
    bg = Image.open('data/assets/ui/ui_background.png')
    gr = Image.open('data/assets/ui/ui_ground.png').convert('RGBA')
    gr_pos = {
        LEFT: (60, 400),
        RIGHT: (720, 400),
    }
    for pos in gr_pos.values():
        bg.paste(gr, pos, gr)
    rt_rect = {
        LEFT: (132, 175, 275, 275),
        RIGHT: (792, 175, 275, 275),
    }
    rts = {
        LEFT: Image.open(os.path.join(ROOSTERS_ROOT, a)).convert('RGBA'),
        RIGHT: Image.open(os.path.join(ROOSTERS_ROOT, b)).convert('RGBA'),
    }
    X, Y, W, H = range(4)
    for r in rts.keys():
        im = rts[r]
        if r == mirror:
            im = ImageOps.mirror(im)
        rect = rt_rect[r]
        im.thumbnail(rt_rect[r][2:])
        pos = rect[X] + (rect[W] - im.width)//2, rect[Y] + rect[H] - im.height
        bg.paste(im, pos, im)
    return bg


if __name__ == '__main__':
    from cmd import Cmd

    class ImagePreviewCmd(Cmd):
        prompt = 'img> '
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
        
        def do_battle(self, args):
            default = 'rooster.png'
            args = args.strip().split(' ')
            a = default
            b = default
            if args[0] != '':
                a = args[0]
                if len(args) > 1:
                    b = args[1]
            create_battle(a, b).show()
        
    ImagePreviewCmd().cmdloop()
