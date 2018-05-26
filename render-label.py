#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

def do_print (width, height, data, stream=sys.stdout.buffer):
   bytes = (width + 7) // 8

   stream.write (b"%c*" % (27, ))          # Restore defaults
   stream.write (b"%cB%c" % (27, 9))       # dot tab 0
   stream.write (b"%cD%c" % (27, bytes))   # Bytes per line
   stream.write (b"%ci" % (27, ))          # Text mode

   # label length
   formlen = int (height)
   stream.write (b"%cL%c%c" % (27, formlen // 256, formlen % 256))

   for i in range (height):
      if data:
         line = data[:bytes]
         data = data[bytes:]
      stream.write (b"\x16" + line)

   for i in range (88 * 2):  # feed to knife
      stream.write (b"\x16" + b"\x00" * bytes)

   stream.write (b"%cE" % (27, ))  # Cut tape



def render_text (text, tapewidth=128, font="Arial, 60", save=None, stream=sys.stdout.buffer):
   import math
   import gi
   import cairo, PIL.Image, io
   gi.require_version('Pango', '1.0')
   gi.require_version('PangoCairo', '1.0')
   from gi.repository import Pango as pango
   from gi.repository import PangoCairo as pangocairo

   surf = cairo.ImageSurface (cairo.FORMAT_A1, 1, 1)
   cr = cairo.Context (surf)
   layout = pangocairo.create_layout (cr)
   layout.set_font_description (pango.FontDescription (font))
   layout.set_markup (text)
   extents = layout.get_pixel_extents ()

   # now do it all again with proper surface dimensions

   width = tapewidth
   height = max (extents.logical_rect.width, extents.ink_rect.width)
   txtwidth = max (extents.logical_rect.height, extents.ink_rect.height)
   y0 = min (extents.logical_rect.x, extents.ink_rect.x)

   surf = cairo.ImageSurface (cairo.FORMAT_A1, width, height)
   cr = cairo.Context (surf)
   cr.set_operator (cairo.OPERATOR_SOURCE)
   cr.set_source_rgba (1, 1, 1, 0)
   cr.paint ()
   cr.set_source_rgba (0, 0, 0, 1)
   cr.rotate (math.pi / 2)
   cr.translate (0, -width)

   layout = pangocairo.create_layout (cr)
   layout.set_font_description (pango.FontDescription (font))
   layout.set_markup (text)

   cr.move_to (-y0, width / 2 - txtwidth / 2)
   pangocairo.show_layout (cr, layout)

   surf.flush ()
   # bah, we need to hack around not implemented features of pycairo...
   f = io.BytesIO ()
   surf.write_to_png (f)

   img = PIL.Image.open (f)
   img = img.convert('1')
   if save:
      img.save(save)
      print("image saved to", save)
   else:
      do_print (width, height, img.tobytes (), stream)

import argparse

if __name__ == '__main__':
   parser = argparse.ArgumentParser(description="Render text for label write and optionally print")
   parser.add_argument("text", nargs='?', help="text to write (default: read from stdin)")
   parser.add_argument("--font", default="Arial, 60", help="font to use (default: 'Arial, 60')")
   parser.add_argument("--tapewidth", default=128, type=int, help="Tape Width (default: 128)")
   parser.add_argument("--save", metavar="FILE", help="save image to filename instead of printing")
   parser.add_argument("--ip", help="talk to printer at IP instead of writing to stdout")
   args = parser.parse_args()
   if args.text is None:
      args.text = input()
   if args.ip:
      if args.save:
         raise Exception("options 'ip' and 'save' conflict")
      import socket
      stream = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_IP)
      print("connecting to {}:{}".format(args.ip, 9100))
      stream.connect((args.ip, 9100))
   else:
      stream = sys.stdout.buffer
   render_text(args.text, font=args.font, tapewidth=args.tapewidth, save=args.save, stream=stream)
   if args.ip:
      time.sleep(4)
      stream.close()
   if 0:
      img = b""
      for i in range (256)[::-1]:
         for j in range (8):
            if i & (1 << j):
               img += b"\xff\xff"
            else:
               img += b"\x00\x00"
      do_print (128, 256, img)
