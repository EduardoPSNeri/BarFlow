from pathlib import Path
import sys,sqlite3
from datetime import datetime
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.database import DB_PATH,DATA_DIR
if not DB_PATH.exists():sys.exit('Banco ainda não foi criado.')
folder=DATA_DIR/'backups';folder.mkdir(parents=True,exist_ok=True)
target=folder/('barflow-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.db')
with sqlite3.connect(DB_PATH) as source,sqlite3.connect(target) as dest:source.backup(dest)
print('Backup concluído:',target)
