from core.logging import setup_logging
from core.materials import MATERIALS_DIR
from db.models import migrate_tables
from seed_database import seed_demo_data


def run_startup_tasks() -> None:
    setup_logging()
    migrate_tables()
    seed_demo_data()
    MATERIALS_DIR.mkdir(exist_ok=True)
