"""YOLOv5 v7.0 の train.py を、torch 2.6 以降で動くように torch.load を weights_only=False に直して呼ぶ。
引数は train.py にそのまま渡す。

    cd <v7.0 の clone> && <venv>/bin/python <このファイル> --weights yolov5x.pt --data ... (train.py の引数)
"""
import os, runpy, sys
import torch
ol = torch.load
torch.load = lambda *x, **k: ol(*x, **{**k, 'weights_only': False})
sys.path.insert(0, os.getcwd())
sys.argv = ['train.py'] + sys.argv[1:]
runpy.run_path('train.py', run_name='__main__')
