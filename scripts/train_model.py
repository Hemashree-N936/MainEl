import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_core.utils.runtime_checks import RuntimeCompatibilityError, validate_training_runtime

try:
    validate_training_runtime()
except RuntimeCompatibilityError as exc:
    raise SystemExit("Runtime validation failed: {0}".format(exc)) from exc

from platform_core.db.init_db import init_db
from platform_core.db.session import SessionLocal
from platform_core.services.ml.model_service import ModelTrainingService


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        result = ModelTrainingService(db).train_and_compare()
        print(result)
    finally:
        db.close()


if __name__ == "__main__":
    main()
