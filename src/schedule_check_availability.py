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


class TimeTable1:
    """
    schedule rules
    1. 6:00 a.m. - 7:00 a.m. : run every 5 minutes
    2. 7:00 a.m. - 9:00 a.m. : run every 2 minutes
    3. 9:00 a.m. - 10:00 a.m. : run every 5 minutes
    4. 10:00 a.m. - 12:00 a.m. : run every 10 minutes
    5. 12:00 a.m. - 22:00 p.m. : run every 20 minutes
    """

    def __init__(self, job, count_schedulers=5) -> None:
        self.job: function = job
        self.schedulers: list[schedule.Scheduler] = []
        self.rule_checkers: dict[schedule.Scheduler, function] = {}

        for i in range(count_schedulers):
            s = schedule.Scheduler()
            s.id = i+1
            self.schedulers.append(s)
            self.__setattr__('s' + str(i + 1), s)

    def clear_all(self):
        for s in self.schedulers:
            s.clear()
        self.current_scheduler = None

    def init_schedules(self):
        self.schedule_test()

    def check_rule(self, func, current_time):
        return func(current_time)

    def schedule_test(self):
        # set rules (test)
        self.rule_checkers[self.s1] = lambda current_time: 2 <= (current_time - start_time).seconds < 5
        self.rule_checkers[self.s2] = lambda current_time: 4 <= (current_time - start_time).seconds < 10
        self.rule_checkers[self.s3] = lambda current_time: 4 <= (current_time - start_time).seconds < 10
        self.rule_checkers[self.s4] = lambda current_time: 10 <= (current_time - start_time).seconds < 13
        self.rule_checkers[self.s5] = lambda current_time: 13 <= (current_time - start_time).seconds < 20
        print("schedule job for s1")
        self.s1.every(1).seconds.do(self.job, msg="Job by s1")
        print("schedule job for s2")
        self.s2.every(2).seconds.do(self.job, msg="Job by s2")
        print("schedule job for s3")
        self.s3.every(1).seconds.do(self.job, msg="Job by s3")
        print("schedule job for s4")
        self.s4.every(1).seconds.do(self.job, msg="Job by s4")
        print("schedule job for s5")
        self.s5.every(3).seconds.do(self.job, msg="Job by s5")

    def run(self, current_time: datetime.time):
        for s in self.schedulers:
            if self.rule_checkers[s](current_time):
                s.run_pending()


class TimeTable:
    def __init__(self, job) -> None:
        self.s = schedule.Scheduler()
        # rules = {
        #   "tag": lambda current_time: if "tag"ed jobs is allowed to run at current_time
        # }
        self.rules: dict[str, function] = {}
        self.job = job
    
    def schedule(self):
        self.rules["1"] = lambda current_time: 2 <= (current_time - start_time).seconds < 5
        self.rules["2"] = lambda current_time: 4 <= (current_time - start_time).seconds < 10
        self.rules["3"] = lambda current_time: 4 <= (current_time - start_time).seconds < 10
        self.rules["4"] = lambda current_time: 10 <= (current_time - start_time).seconds < 13
        self.rules["5"] = lambda current_time: 13 <= (current_time - start_time).seconds < 20
        print("schedule job for rule 1")
        self.s.every(1).seconds.do(self.job, msg="Job by s1").tag("1")
        print("schedule job for rule 2")
        self.s.every(2).seconds.do(self.job, msg="Job by s2").tag("2")
        print("schedule job for rule 3")
        self.s.every(1).seconds.do(self.job, msg="Job by s3").tag("3")
        print("schedule job for rule 4")
        self.s.every(1).seconds.do(self.job, msg="Job by s4").tag("4")
        print("schedule job for rule 5")
        self.s.every(3).seconds.do(self.job, msg="Job by s5").tag("5")

    def run(self, current_time: datetime.time):
        for tag, rule_checker in self.rules.items():
            if rule_checker(current_time):
                jobs = self.s.get_jobs(tag)
                for job in jobs:
                    if job.should_run:
                        job.run()


if __name__ == "__main__":
    schedule.every(5).to(10).minutes.do(real_job, product=models["desert-256g"])
    schedule.every(5).to(10).minutes.do(real_job, randomly=True)
    # schedule.every(3).to(6).seconds.do(real_job)
    # schedule.every(3).to(6).seconds.do(real_job, product=models["desert-256g"])
    # schedule.every(5).seconds.do(real_job, randomly=True)

    print("scheduled!")

    while True:
        schedule.run_pending()
        time.sleep(1)


if False:
    tb = TimeTable(log_job)
    tb.schedule()

    while True:
        now = datetime.now()
        tick = (now - start_time).seconds
        print("tick:", tick)
        tb.run(now)
        time.sleep(1)
        if tick > 30:
            break
