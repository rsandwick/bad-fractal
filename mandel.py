import collections
import colorsys
import logging
import numpy
import os
import pygame
import threading
import time
import Tkinter as tk

MAX_ITERATIONS = 100

def rgb_ramp():
    for i in xrange(MAX_ITERATIONS):
        rgb = colorsys.hsv_to_rgb(
                i / (1. * MAX_ITERATIONS),
                1., 0.5 + (i / (2. * MAX_ITERATIONS)))
        #rgb = colorsys.hls_to_rgb(
        #        0.66667 - (i / (2. * MAX_ITERATIONS)),
        #        0.25 + (0.75 * i / (1. * MAX_ITERATIONS)), 1.)
        yield pygame.Color(*(int(x * 255) for x in rgb))

colors = list(rgb_ramp())

class Point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

def mandel(n, m, xmin, xmax, ymin, ymax):
    ix, iy = numpy.mgrid[0:n, 0:m]
    c = (numpy.linspace(xmin, xmax, n, dtype=numpy.float64)[ix] +
         1j * numpy.linspace(ymin, ymax, m, dtype=numpy.float64)[iy])
    img = numpy.zeros(c.shape, dtype=numpy.uint32)
    ix.shape = n * m
    iy.shape = n * m
    c.shape = n * m
    z = numpy.copy(c)
    prev_color = colors[0]
    for color in colors:
        if not len(z):
            break
        numpy.multiply(z, z, z)
        numpy.add(z, c, z)
        abs_z = numpy.abs(z)
        #rem = abs_z > 2.0
        rem = abs_z > 256.0
        nu = numpy.log2(numpy.log2(abs_z[rem])) % 1
        r = (nu * prev_color.r) + ((-nu + 1) * color.r)
        g = (nu * prev_color.g) + ((-nu + 1) * color.g)
        b = (nu * prev_color.b) + ((-nu + 1) * color.b)
        img[ix[rem], iy[rem]] = (
                (r.astype(numpy.uint32) << 16) +
                (g.astype(numpy.uint32) << 8) +
                (b.astype(numpy.uint32)))
        yield img
        prev_color = color
        rem = -rem
        z = z[rem]
        ix = ix[rem]
        iy = iy[rem]
        c = c[rem]

class MandelbrotFrame(tk.Frame):

    screen = None
    zoom = 1.
    center = Point(-.75, 0.)

    def __init__(self, master=None, height=400, width=400, **kwargs):
        self.height = height
        self.width = width
        self.font = pygame.font.SysFont("Segoe UI", 16, bold=True)
        self._cancel_event = threading.Event()
        tk.Frame.__init__(
                self, master=master, height=height, width=width, **kwargs)
        self.bind("<Configure>", self.on_resize)

    def _set_mode(self):
        self.screen = pygame.display.set_mode(
                (self.width, self.height), pygame.RESIZABLE)

    def on_resize(self, event):
        self._set_mode()
        self.draw()

    def showtext(self, x, y, s, *args):
        self.screen.blit(self.font.render(
                s % args, True, (255, 255, 255)), (x, y))

    def draw(self):
        start = time.time()
        ratio = self.width / float(self.height)
        center, zoom = self.center, self.zoom
        self._cancel_event.clear()
        for i, tex in enumerate(mandel(
                self.width, self.height,
                center.x - (ratio * zoom),
                center.x + (ratio * zoom),
                center.y - zoom,
                center.y + zoom), start=1):
            try:
                pygame.surfarray.blit_array(self.screen, tex)
                self.showtext(
                        12, 8, "x=%g y=%g zoom=%g", center.x, center.y, zoom)
            except TypeError:
                self._set_mode()
                pygame.surfarray.blit_array(self.screen, tex)
                self.showtext(
                        12, 8, "x=%g y=%g zoom=%g", center.x, center.y, zoom)
            self.showtext(
                    12, self.height - 32, "render=%.3fs iteration=%d",
                    time.time() - start, i)
            pygame.display.flip()
            if self._cancel_event.is_set():
                break
        self.master.update()

    def zoom_in(self, event):
        self._cancel_event.set()
        self.zoom /= 2.
        self.draw()
    def zoom_out(self, event):
        self._cancel_event.set()
        self.zoom *= 2.
        self.draw()
    def move_left(self, event):
        self._cancel_event.set()
        self.center.x -= (self.width / float(self.height)) * self.zoom / 8.
        self.draw()
    def move_right(self, event):
        self._cancel_event.set()
        self.center.x += (self.width / float(self.height)) * self.zoom / 8.
        self.draw()
    def move_up(self, event):
        self._cancel_event.set()
        self.center.y -= self.zoom / 8.
        self.draw()
    def move_down(self, event):
        self._cancel_event.set()
        self.center.y += self.zoom / 8.
        self.draw()

def main():
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("mandel")

    pygame.font.init()

    root = tk.Tk()
    root.title("badass f-ing fractal")
    embed = MandelbrotFrame(root, width=800, height=600)
    embed.grid(column=0, row=0, sticky=(tk.N + tk.S + tk.E + tk.W))
    embed.pack()

    root.bind("<Left>", embed.move_left)
    root.bind("<Right>", embed.move_right)
    root.bind("<Up>", embed.move_up)
    root.bind("<Down>", embed.move_down)
    root.bind("<plus>", embed.zoom_in)
    root.bind("<minus>", embed.zoom_out)

    os.environ["SDL_WINDOWID"] = str(embed.winfo_id())
    os.environ["SDL_VIDEODRIVER"] = "windib"
    #os.environ["SDL_VIDEODRIVER"] = "directx"

    root.mainloop()

if __name__ == "__main__":
    main()
