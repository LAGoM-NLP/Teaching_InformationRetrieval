import os
from pathlib import Path
PATH_PACKAGE = Path(__file__).resolve().parent
PATH_SRC     = PATH_PACKAGE.parent
IS_EDITABLE_INSTALL = PATH_SRC.stem == "src"

if IS_EDITABLE_INSTALL:
    PATH_ROOT = PATH_SRC.parent
else:
    PATH_ROOT = Path(os.getcwd())

PATH_DATA     = PATH_ROOT / "data"
PATH_DATA_IN  = PATH_DATA / "in"
PATH_DATA_OUT = PATH_DATA / "out"
PATH_DATA_OUT.mkdir(exist_ok=True, parents=True)

from fiject import setFijectOutputFolder
setFijectOutputFolder(PATH_DATA_OUT)
