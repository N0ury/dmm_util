# __main__.py

import sys

if sys.version_info[0] < 3 or sys.version_info[1] < 10:
  print ('Python version 3.10 or later is needed. Please consider upgrading')
  sys.exit(1)

from fluke_28x_dmm_util import dmm_util

def cli():
  """Call the utility"""
  dmm_util.main()

if __name__ == "__main__":
  cli()
