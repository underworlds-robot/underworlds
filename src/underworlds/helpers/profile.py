from functools import wraps
import time

PROFILING_ENABLED=False

def profile(f):

    if not PROFILING_ENABLED:
        return f

    try:
        name = f.__qualname__ # python3
    except:
        name = f.__module__ + "." + f.__name__ # python3

    @wraps(f)
    def wrapper(*args, **kwargs):

        stime=time.time();print("PROFILE;%f;enter %s" % (stime,name))

        res=f(*args, **kwargs)

        endtime=time.time();print("PROFILE;%f;exit %s;%.2f" % (endtime,name,(endtime-stime)*1000))
        return res

    return wrapper

def profileonce(msg):
    if not PROFILING_ENABLED:
        return
    print("PROFILE;%f;%s" % (time.time(),msg))
