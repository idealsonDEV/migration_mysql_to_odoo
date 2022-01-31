import sys
import logging

root = logging.getLogger('root')
root.setLevel(logging.INFO)
root.propagate = False
handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
root.addHandler(handler)
root.addFilter(lambda record: record.levelno == logging.INFO)