import pkgutil


__version__ = pkgutil.get_data('cddagl', 'VERSION').decode("utf8").strip()
