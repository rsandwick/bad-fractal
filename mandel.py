import colorsys
import logging
import numpy
import os
import pygame
import threading
import time

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

class MandelbrotViewer(object):

    screen = None
    x = -.75
    y = 0.
    zoom = 1.

    def __init__(self, master=None, height=400, width=400, **kwargs):
        self.height = height
        self.width = width
        self.font = pygame.font.SysFont("Segoe UI", 16, bold=True)
        self._cancel_event = threading.Event()

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
        x, y, zoom = self.x, self.y, self.zoom
        self._cancel_event.clear()
        for i, tex in enumerate(mandel(
                self.width, self.height,
                x - (ratio * zoom), x + (ratio * zoom),
                y - zoom, y + zoom), start=1):
            try:
                pygame.surfarray.blit_array(self.screen, tex)
                self.showtext(12, 8, "x=%g y=%g zoom=%g", x, y, zoom)
            except TypeError:
                self._set_mode()
                pygame.surfarray.blit_array(self.screen, tex)
                self.showtext(12, 8, "x=%g y=%g zoom=%g", x, y, zoom)
            self.showtext(
                    12, self.height - 32, "render=%.3fs iteration=%d",
                    time.time() - start, i)
            pygame.display.flip()
            if self._cancel_event.is_set():
                break

    def zoom_in(self):
        self._cancel_event.set()
        self.zoom /= 2.
        self.draw()
    def zoom_out(self):
        self._cancel_event.set()
        self.zoom *= 2.
        self.draw()
    def move_left(self):
        self._cancel_event.set()
        self.x -= (self.width / float(self.height)) * self.zoom / 8.
        self.draw()
    def move_right(self):
        self._cancel_event.set()
        self.x += (self.width / float(self.height)) * self.zoom / 8.
        self.draw()
    def move_up(self):
        self._cancel_event.set()
        self.y -= self.zoom / 8.
        self.draw()
    def move_down(self):
        self._cancel_event.set()
        self.y += self.zoom / 8.
        self.draw()

def main():
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("mandel")

    #os.environ["SDL_VIDEODRIVER"] = "windib"
    os.environ["SDL_VIDEODRIVER"] = "directx"

    pygame.display.init()
    pygame.display.set_caption("badass f-ing fractal")
    pygame.font.init()

    viewer = MandelbrotViewer(width=800, height=600)
    viewer.draw()

    done = False
    while not done:
        for event in pygame.event.get():
            logger.debug("%s", event)
            if event.type == pygame.QUIT:
                done = True
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_UP:
                    viewer.move_up()
                elif event.key == pygame.K_DOWN:
                    viewer.move_down()
                elif event.key == pygame.K_LEFT:
                    viewer.move_left()
                elif event.key == pygame.K_LEFT:
                    viewer.move_right()
                elif event.key == pygame.K_PAGEUP:
                    viewer.zoom_in()
                elif event.key == pygame.K_PAGEDOWN:
                    viewer.zoom_out()
                elif event.key == pygame.K_ESCAPE:
                    done = True

if __name__ == "__main__":
    main()
