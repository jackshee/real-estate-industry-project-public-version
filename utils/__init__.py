# Lazy imports to avoid dependency issues
def __getattr__(name):
    if name == "GeoUtils":
        from .geo import GeoUtils

        return GeoUtils
    elif name == "DownloadUtils":
        from .download import DownloadUtils

        return DownloadUtils
    elif name == "PreprocessUtils":
        from .preprocess import PreprocessUtils

        return PreprocessUtils
    elif name == "LoadUtils":
        from .load import LoadUtils

        return LoadUtils
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = ["GeoUtils", "DownloadUtils", "PreprocessUtils", "LoadUtils"]
