#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import sys
from OpenGL.GLUT import * # to get time and compute FPS


import underworlds
from underworlds.tools.visibility import VisibilityMonitor


def main(world, camera = None):
    benchmark = False

    with underworlds.Context("Visibility Monitor") as ctx:
        visibility = VisibilityMonitor(ctx, ctx.worlds[world])

        # for FPS computation
        frames = 0
        last_fps_time = glutGet(GLUT_ELAPSED_TIME)

        try:
            while True:

                if benchmark:
                    # Compute FPS
                    gl_time = glutGet(GLUT_ELAPSED_TIME)
                    frames += 1
                    delta = gl_time - last_fps_time
                

                    if delta >= 1000:
                        fps = (frames * 1000 / delta)
                        update_delay = (delta / frames)

                        print("\x1b[1FUpdate every %.2fms - %.0f fps" % (update_delay, fps))
                        frames = 0
                        last_fps_time = gl_time

                if camera:
                    objs = {camera: visibility.from_camera(camera)}
                else:
                    objs = visibility.compute_all()

                printed_lines = 0
                for c, seen in objs.items():
                    printed_lines += 1
                    print("Camera %s:\t\t%d objects visible" % (c, len(seen)))
                    for n in seen:
                        printed_lines += 1
                        print(" - %s" % n)

                print('\x1b[%dF' % (printed_lines + 1)) # move the console cursor up.

                if not benchmark:
                    visibility.scene.waitforchanges(0.2)

        except KeyboardInterrupt:
            pass

        print("\x1b[%dE" % len(visibility.cameras))
        print("Quitting")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("world", help="Underworlds world to monitor")
    parser.add_argument("--camera", "-c", default=None, help="The camera to check visibility from (default: all)")
    args = parser.parse_args()

    main(args.world, args.camera)


