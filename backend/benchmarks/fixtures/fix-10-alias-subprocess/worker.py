import subprocess as sp

def do_work(cmd):
    sp.run(cmd, shell=True)
