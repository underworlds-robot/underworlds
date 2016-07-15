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

        sys.stdout.write("\x1b[s") # saves cursor position

        try:
            while True:
                sys.stdout.write('\x1b[0J') # clear terminal to bottom of screen.

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


                for c, seen in objs.items():
                    print("Camera %s:\t\t%d objects visible" % (c, len(seen)))
                    for n in seen:
                        print(" - %s" % n)

                sys.stdout.write('\x1b[u') # move the console cursor back to initial position

                if not benchmark:
                    visibility.scene.waitforchanges(0.2)

        except KeyboardInterrupt:
            pass

        sys.stdout.write('\x1b[u') # move the console cursor back to initial position
        sys.stdout.write('\x1b[0J') # clear terminal to bottom of screen.
        print("Quitting")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("world", help="Underworlds world to monitor")
    parser.add_argument("--camera", "-c", default=None, help="The camera to check visibility from (default: all)")
    args = parser.parse_args()

    main(args.world, args.camera)


