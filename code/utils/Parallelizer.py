import multiprocessing

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from utils.log import _info, _debug, _warning, _error, _exception
from multiprocessing import Process, Queue, JoinableQueue, Manager
import time

class Parallelizer:
    def __init__(self, func, thread_count, config=False, data=False):
        self.config = config
        self.data = data
        self.processes = []
        self.q = JoinableQueue()
        self.multi_process_manager = Manager()
        self.return_dict = self.multi_process_manager.list()

        _info("corsica.fpgen.par", "Starting {} threads for function {}".format(thread_count, func.__name__))
        for thread_nr in range(0, thread_count):
            p = Process(target=self._worker, args=(thread_nr, self.return_dict, func))
            p.start()
            self.processes.append(p)

    def work(self, items):
        res = []
        _info("corsica.fpgen.par", "Adding {} Items".format(len(items)))
        for item in items:
            self.q.put(item)
        self.q.join()
        _info("corsica.fpgen.par", "Terminating Processes")
        for process in self.processes:
            process.terminate()
        return list(self.return_dict)

    def _worker(self, thread_nr, return_dict, func):
        if self.config:
            db_conn_str = 'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'.format(**self.config['mysql'])
            db_engine = create_engine(db_conn_str, pool_timeout=20, pool_recycle=299, pool_pre_ping=True)
            db_session = sessionmaker(bind=db_engine)()
        try:

            while True:
                try:
                    item = self.q.get()
                    if not item:
                        continue
                    if self.config and self.data:
                        ret = func(item, db_session, self.data)
                    elif self.config:
                        ret = func(item, db_session)
                    else:
                        ret = func(item)

                    return_dict.append(ret)

                    self.q.task_done()
                except KeyboardInterrupt:
                    break
        except Exception as e:
            _error('corsica.fpgen.par', 'Job Error {}'.format( type(e).__name__, e))
            _exception('corsica.tests.dae', e)
        finally:
            db_session.close()
