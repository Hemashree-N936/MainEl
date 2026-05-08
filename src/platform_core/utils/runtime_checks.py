from importlib import metadata
from typing import Optional, Tuple


class RuntimeCompatibilityError(RuntimeError):
    pass


def require_package_version(package_name: str, minimum: Tuple[int, int, int]) -> str:
    version = package_version(package_name)
    if version is None:
        raise RuntimeCompatibilityError(
            "{0} is not installed. Run pip install -r requirements.txt.".format(package_name)
        )
    if not version_at_least(version, minimum):
        raise RuntimeCompatibilityError(
            "{0}>={1} is required, but {2} is installed. Run pip install -r requirements.txt.".format(
                package_name,
                ".".join(str(part) for part in minimum),
                version,
            )
        )
    return version


def package_version(package_name: str) -> Optional[str]:
    try:
        return metadata.version(package_name)
    except metadata.PackageNotFoundError:
        return None


def version_at_least(version: str, minimum: Tuple[int, int, int]) -> bool:
    parts = []
    for token in version.replace("-", ".").split("."):
        if token.isdigit():
            parts.append(int(token))
        else:
            numeric = "".join(character for character in token if character.isdigit())
            parts.append(int(numeric) if numeric else 0)
        if len(parts) == 3:
            break
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3]) >= minimum


def validate_training_runtime() -> None:
    require_package_version("SQLAlchemy", (2, 0, 0))
    require_package_version("pandas", (2, 0, 0))
    require_package_version("scikit-learn", (1, 5, 0))
    require_package_version("joblib", (1, 0, 0))

