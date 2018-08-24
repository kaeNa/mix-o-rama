from datetime import datetime


def make_timeout(delay_ms):
    starttime = datetime.now().timestamp()

    def time_is_out():
        return datetime.now().timestamp() > starttime + (delay_ms/1000)

    return time_is_out
