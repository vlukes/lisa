#! /usr/bin/python
# -*- coding: utf-8 -*-

import subprocess


import logging
logger = logging.getLogger(__name__)







def update():
    # update submodules codes
    print ('Updating submodules')
    try:
        #import pdb; pdb.set_trace()
        subprocess.call('git pull', shell=True)
        subprocess.call('git submodule update --init --recursive', shell=True)

    except:
        print ('Probem with git submodules')


def main():
    logger = logging.getLogger()

    logger.setLevel(logging.WARNING)
    ch = logging.StreamHandler()
    logger.addHandler(ch)
    update()
                        
if __name__ == "__main__":
    main()
