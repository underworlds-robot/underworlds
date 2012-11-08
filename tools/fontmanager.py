"""
    font.py -- Displays FPS in OpenGL using TrueType fonts.

    Copyright (c) 2002. Nelson Rush. All rights reserved.

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.
"""

from OpenGL.GL import *
import pygame.font
import pygame.image

class FontManager:
    def __init__(self, fontname, width, height, fontsize = 18):

        self.w = width
        self.h = height
        pygame.font.init()
        if not pygame.font.get_init():
            print 'Could not render font.'
            raise Exception("Error while initializing the font rendering engine")

        self.font = pygame.font.Font(fontname, fontsize)
        self.char = []
        for c in range(256):
            self.char.append(self.CreateCharacter(chr(c)))
        self.char = tuple(self.char)
        self.lw = self.char[ord('0')][1]
        self.lh = self.char[ord('0')][2]

    def CreateCharacter(self, s):
        try:
            letter_render = self.font.render(s, 1, (255,255,255), (0,0,0))
            letter = pygame.image.tostring(letter_render, 'RGBA', 1)
            letter_w, letter_h = letter_render.get_size()
        except:
            letter = None
            letter_w = 0
            letter_h = 0
        return (letter, letter_w, letter_h)

    def display(self, text, x, y):
        s = str(text)
        i = 0
        lx = 0
        length = len(s)
        glPushMatrix()
        while i < length:
            glRasterPos2i(x + lx, y)
            ch = self.char[ ord( s[i] ) ]
            glDrawPixels(ch[1], ch[2], GL_RGBA, GL_UNSIGNED_BYTE, ch[0])
            lx += ch[1]
            i += 1
        glPopMatrix()

    def __del__(self):
        pygame.font.quit()
