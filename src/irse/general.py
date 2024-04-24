from pathlib import Path
PATH_ROOT = Path(__file__).resolve().parent.parent
PATH_DATA = PATH_ROOT / "data"
PATH_DATA_IN = PATH_DATA / "in"
PATH_DATA_OUT = PATH_DATA / "out"
PATH_DATA_OUT.mkdir(exist_ok=True, parents=True)

from fiject import setFijectOutputFolder
setFijectOutputFolder(PATH_DATA_OUT)
