import os
import inspect
import sys
import logging
from os import getcwd
from glob import glob
from django.urls import path, re_path
from django.views.generic.base import View


def get_recursive_files(path, files):
    """
    Get all the files from a given path.
    """
    if not os.path.isfile(path):
        for directory_member in glob(os.path.join(path, '*')):
            if '__' in directory_member:
                continue

            if '.py' in directory_member:
                files.append(directory_member)

            get_recursive_files(directory_member, files)


def get_decorated_classes(routes_folder=getcwd()):
    """
    Get all the decorated classes in a given path.

    :param routes_folder: The folder which we need to look decorated routes.
        By default the value of the os.getcwd()
    """
    files = []
    get_recursive_files(routes_folder, files)

    routes = []
    for file in files:
        # Go over the files we got and compile an import path.
        import_path = file.replace(routes_folder + os.path.sep, '') \
            .replace('.py', '') \
            .replace(os.path.sep, '.')

        try:
            # Import the module and inspect the members (the object which were
            # imported).

            __import__(import_path)

            for name, obj in inspect.getmembers(sys.modules[import_path]):
                if not inspect.isclass(obj):
                    # This is not a class. Skip.
                    continue

                if not issubclass(obj, View):
                    continue

                try:
                    routes.append({'path': obj.decorated_url_data, 'object': obj})
                except Exception as e:
                    # todo: Don't fail on exception.
                    logging.info(e)

        except Exception as e:
            # todo: Don't fail on exception.
            logging.info(e)

    return routes


def auto_register(urlpatterns):
    """
    Appending url patterns to the urlpatterns variable we pass from the url.py
    file.
    """

    routes = get_decorated_classes()

    for route in routes:

        if 're_path' in route['path']:
            # Setting the handler the pattern for a regex handler.
            pattern = route['path']['re_path']
            handler = re_path
        else:
            handler = path
            pattern = route['path']['path']

        # Setting some variables.
        name = route['path'].get('name', None)
        extra = route['path'].get('extra', {})
        url_pattern = handler(
            pattern,
            route['object'].as_view(),
            extra,
            name=name,
        )
        urlpatterns.append(url_pattern)
