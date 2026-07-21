from concurrent.futures import ThreadPoolExecutor
from .utils import CountUpDownLatch
import threading
import logging
import multiprocessing
import os
import logging.handlers
from .exceptions import  FileNotFoundError
try:
    from queue import Empty     # Python 3
    import _thread
except ImportError:
    from Queue import Empty     # Python 2
    import thread

WORKER_THREAD_PER_PROCESS = 50
QUEUE_BUCKET_SIZE = 10
END_QUEUE_SENTINEL = [None, None]
GLOBAL_EXCEPTION = None
GLOBAL_EXCEPTION_LOCK = threading.Lock()


def monitor_exception(exception_queue, process_ids):
    global GLOBAL_EXCEPTION
    logger = logging.getLogger("azure.datalake.store")

    while True:
        try:
            local_exception = exception_queue.get(timeout=0.1)
            if local_exception == END_QUEUE_SENTINEL:
                break
            logger.log(logging.DEBUG, "Setting global exception")
            GLOBAL_EXCEPTION_LOCK.acquire()
            GLOBAL_EXCEPTION = local_exception
            GLOBAL_EXCEPTION_LOCK.release()
            logger.log(logging.DEBUG, "Closing processes")
            for p in process_ids:
                p.terminate()
            logger.log(logging.DEBUG, "Joining processes")
            for p in process_ids:
                p.join()

            logger.log(logging.DEBUG, "Interrupting main")
            raise Exception(local_exception)
        except Empty:
            pass


def log_listener_process(queue):
    while True:
        try:
            record = queue.get(timeout=0.1)
            queue.task_done()
            if record == END_QUEUE_SENTINEL:  # We send this as a sentinel to tell the listener to quit.
                break
            logger = logging.getLogger("azure.datalake.store")
            #logger.handlers.clear()
            logger.handle(record)   # No level or filter logic applied - just do it!
        except Empty:               # Try again
            pass
        except Exception as e:
            import sys, traceback
            print('Problems in logging')
            traceback.print_exc(file=sys.stderr)


def multi_processor_change_acl(adl, path=None, method_name="", acl_spec="", number_of_sub_process=None):
    logger = logging.getLogger("azure.datalake.store")

    def launch_processes(number_of_processes):
        if number_of_processes is None:
            number_of_processes = max(2, multiprocessing.cpu_count() - 1)
        process_list = []
        for i in range(number_of_processes):
            process_list.append(multiprocessing.Process(target=processor,
                                    args=(adl, file_path_queue, finish_queue_processing_flag,
                                          method_name, acl_spec, log_queue, exception_queue)))
            process_list[-1].start()
        return process_list

    def walk(walk_path):
        try:
            paths = []
            all_files = adl.ls(path=walk_path, detail=True)

            for files in all_files:
                if files['type'] == 'DIRECTORY':
                    dir_processed_counter.increment()               # A new directory to process
                    walk_thread_pool.submit(walk, files['name'])

                paths.append((files['name'], files['type'] == 'FILE'))

                if len(paths) == QUEUE_BUCKET_SIZE:
                    file_path_queue.put(list(paths))
                    paths = []

            if paths != []:
                file_path_queue.put(list(paths))  # For leftover paths < bucket_size
        except FileNotFoundError:
            pass                    # Continue in case the file was deleted in between
        except Exception:
            import traceback
            logger.exception("Failed to walk for path: " + str(walk_path) + ". Exiting!")
            exception_queue.put(traceback.format_exc())
        finally:
            dir_processed_counter.decrement()           # Processing complete for this directory

    # Initialize concurrency primitives
    log_queue = multiprocessing.JoinableQueue()
    exception_queue = multiprocessing.Queue()
    finish_queue_processing_flag = multiprocessing.Event()
    file_path_queue = multiprocessing.JoinableQueue()
    dir_processed_counter = CountUpDownLatch()

    # Start relevant threads and processes
    log_listener = threading.Thread(target=log_listener_process, args=(log_queue,))
    log_listener.start()
    child_processes = launch_processes(number_of_sub_process)
    exception_monitor_thread = threading.Thread(target=monitor_exception, args=(exception_queue, child_processes))
    exception_monitor_thread.start()
    walk_thread_pool = ThreadPoolExecutor(max_workers=WORKER_THREAD_PER_PROCESS)

    # Root directory needs to be explicitly passed
    file_path_queue.put([(path, False)])
    dir_processed_counter.increment()

    # Processing starts here
    walk(path)

    if dir_processed_counter.is_zero():  # Done processing all directories. Blocking call.
        walk_thread_pool.shutdown()
        file_path_queue.close()          # No new elements to add
        file_path_queue.join()           # Wait for operations to be done
        logger.log(logging.DEBUG, "file path queue closed")
        finish_queue_processing_flag.set()  # Set flag to break loop of child processes
        for child in child_processes:  # Wait for all child process to finish
            logger.log(logging.DEBUG, "Joining process: "+str(child.pid))
            child.join()

    # Cleanup
    logger.log(logging.DEBUG, "Sending exception sentinel")
    exception_queue.put(END_QUEUE_SENTINEL)
    exception_monitor_thread.join()
    logger.log(logging.DEBUG, "Exception monitor thread finished")
    logger.log(logging.DEBUG, "Sending logger sentinel")
    log_queue.put(END_QUEUE_SENTINEL)
    log_queue.join()
    log_queue.close()
    logger.log(logging.DEBUG, "Log queue closed")
    log_listener.join()
    logger.log(logging.DEBUG, "Log thread finished")


def processor(adl, file_path_queue, finish_queue_processing_flag, method_name, acl_spec, log_queue, exception_queue):
    logger = logging.getLogger("azure.datalake.store")
    logger.setLevel(logging.DEBUG)
    removed_default_acl_spec = ",".join([x for x in acl_spec.split(',') if not x.lower().startswith("default")])

    try:
        logger.addHandler(logging.handlers.QueueHandler(log_queue))
        logger.propagate = False                                                        # Prevents double logging
    except AttributeError:
        # Python 2 doesn't have Queue Handler. Default to best effort logging.
        pass

    try:
        func_table = {"mod_acl": adl.modify_acl_entries, "set_acl": adl.set_acl, "rem_acl": adl.remove_acl_entries}
        function_thread_pool = ThreadPoolExecutor(max_workers=WORKER_THREAD_PER_PROCESS)
        adl_function = func_table[method_name]
        logger.log(logging.DEBUG, "Started processor pid:"+str(os.getpid()))

        def func_wrapper(func, path, spec):
            try:
                func(path=path, acl_spec=spec)
            except FileNotFoundError:
                logger.exception("File "+str(path)+" not found")
                # Complete Exception is being logged in the relevant acl method. Don't print exception here
            except Exception as e:
                logger.exception("File " + str(path) + " not set. Exception "+str(e))

            logger.log(logging.DEBUG, "Completed running on path:" + str(path))

        while finish_queue_processing_flag.is_set() == False:
            try:
                file_paths = file_path_queue.get(timeout=0.1)
                file_path_queue.task_done()                 # Will not be called if empty
                for file_path in file_paths:
                    is_file = file_path[1]
                    if is_file:
                        spec = removed_default_acl_spec
                    else:
                        spec = acl_spec

                    logger.log(logging.DEBUG, "Starting on path:" + str(file_path))
                    function_thread_pool.submit(func_wrapper, adl_function, file_path[0], spec)
            except Empty:
                pass

    except Exception as e:
        import traceback
        logger.exception("Exception in pid "+str(os.getpid())+"Exception: " + str(e))
        exception_queue.put(traceback.format_exc())
    finally:
        function_thread_pool.shutdown()  # Blocking call. Will wait till all threads are done executing.
        logger.log(logging.DEBUG, "Finished processor pid: " + str(os.getpid()))
