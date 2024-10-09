from datetime import datetime
import time

import schedule

from check_availability import (
    check_product_availability,
    check_availability,
    models
)


def real_job(product=None, randomly=False):
    current_time = datetime.now()
    print(current_time.isoformat())
    try:
        if randomly:
            check_availability(randomly=randomly)
        else:
            check_product_availability(product)
    except RuntimeError as e:
        print(e)


start_time = datetime.now()


if __name__ == "__main__":
    s1: schedule.Scheduler = schedule.Scheduler()
    # s1.allow_at = lambda t: '06:00' <= t.time().strftime("%H:%M") < "22:00"
    s1.allow_at = lambda t: True
    s1.every(1).to(3).minutes.do(real_job, product=models["desert-256g"])
    s1.every(2).to(5).minutes.do(real_job, randomly=True)
    # test
    # s1.every(3).to(5).seconds.do(real_job, randomly=True)

    s2 = schedule.Scheduler()
    s2.allow_at = lambda t: '07:00' <= t.time().strftime("%H:%M") < "09:30"
    s2.every(15).to(60).seconds.do(real_job, randomly=True)
    s2.every(10).to(30).seconds.do(real_job, product=models["desert-256g"])

    print("scheduled!")

    while True:
        current_time = datetime.now()

        for s in (s1, s2):
            if s.allow_at(current_time):
                s.run_pending()
                time.sleep(0.2)

        time.sleep(1)
