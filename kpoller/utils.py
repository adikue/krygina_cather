import time
import logging
import traceback

from functools import wraps


def safe_retry(cls_meth, attempts=10, retry_time=10):
    @wraps(cls_meth)
    def wrap(*args, **kwargs):
        zelf = args[0]
        zelf_cls = cls_meth.im_class
        zelf_cls_kwargs = {arg: getattr(zelf, arg)
                           for arg in zelf_cls.INIT_ARGS}
        meth_name = cls_meth.__name__

        for i in xrange(attempts):
            logger = getattr(zelf, 'logger', logging.getLogger(__file__))
            logger.info("Attempt to call %s.%s #%s" % (zelf_cls.__name__,
                                                       meth_name, i + 1))
            try:
                meth = getattr(zelf, meth_name)
                noself_args = args[1:]  # remove self
                meth_ret = meth(*noself_args, **kwargs)
            except Exception:
                logger.error("Exception occurred: {%s}"
                             % traceback.format_exc())
                try:
                    new_zelf = zelf_cls(**zelf_cls_kwargs)
                    zelf = new_zelf
                except Exception:
                    logger.info("Failed to reinit %s" % zelf_cls.__name__)
                    raise
                else:
                    logger.info("Successful reinit of %s" % zelf_cls.__name__)
            else:
                break
            logger.info("Will sleep for %s before another retry" % retry_time)
            time.sleep(retry_time)
        else:
            raise
        return zelf, meth_ret
    return wrap


def get_public_ip():
    import requests
    return requests.get('http://ip.42.pl/raw').text
