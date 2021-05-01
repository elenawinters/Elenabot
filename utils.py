"""
    I always forget what these are meant to do.

    We can't import our logger here due to circular import.

"""

from core.color import trace
import traceback
import inspect
import logging
import random
import string
import types
import sys
import re
import os


class Utils:
    def __init__(self):
        pass

    class Enums:
        def __init__(self, enum):
            self.enum = enum

        def find(self, item, default='default'):
            return getattr(self.enum, item, default)

    # class Traceback:
    #     def __init__(self, exc):
    #         self.exc = exc

    #     def formatted(self, tb):
    #         new_frames = []  # old code https://stackoverflow.com/a/37059072
    #         for x in traceback.extract_tb(tb):
    #             frame = list(x)
    #             frame[0] = frame[0].replace(util.abspath(), '.')
    #             new_frames.append(tuple(frame))

    #         return traceback.StackSummary.from_list(new_frames)

    #     def code(self):
    #         exc = sys.exc_info()
    #         print(exc)
    #         formatted = self.formatted(sys.exc_info()[2])
    #         random.seed(str(formatted))
    #         number = random.randint(10000, 99999)

    #         # test = traceback.walk_tb(formatted)
    #         # print(test)
    #         # test2 = traceback.StackSummary.extract(traceback.walk_tb())
    #         # print(test2)
    #         test3 = traceback.StackSummary.extract(traceback.walk_tb(exc[2]))
    #         print(test3)

    #         # test = traceback.format_exception(exc[0], exc[1], formatted)
    #         # test = traceback.format_exception(exc[0], exc[1], formatted)
    #         # print(test)
    #         return {'msg': f'Code #{number}', 'exc_info': (exc[0], exc[1], test3)}

    #     def trace(self):
    #         return [x for x in sys.exc_info()]

    #     def short(self):
    #         err = self.trace()
    #         return f"{err[0].__name__}: {err[1]}"

    def crypt(self, s):
        x = []
        for i in range(len(s)):
            j = ord(s[i])
            if 33 <= j <= 126:
                x.append(chr(33 + ((j + 14) % 94)))
            else:
                x.append(s[i])
        return ''.join(x)

    # def excepthook(self, exctype, value, tb):
    #     log = logging.getLogger('stitches')  # does this even work?
    #     log.exception(**self.Traceback((exctype, value, tb)).code())

    def hack_the_planet(self, ignore: list = []):  # This is overly complicated.
        """ This returns every function from the class it was executed from """
        frame = inspect.stack()[1][0]
        ignores = [frame.f_code.co_name] + ignore
        funcs = []
        for name, run in inspect.getmembers(frame.f_locals['self'].__class__):
            if isinstance(run, types.FunctionType) or isinstance(run, types.MethodType):
                if name not in ignores and not name.startswith('__') and not name.endswith('__'):
                    funcs.append(run)
        return funcs

    def match(self, obj, key):
        """This is mainly meant for dicts with tuples as the key, to find the value"""
        for k, v in obj.items():
            if isinstance(k, str):
                if key == k:
                    return k, v
            else:
                # [return v, k for x in k if find == x]
                for x in k:
                    if key == x:
                        return k, v
        # print('no match')
        return  # We don't return anything

    def random_string(self, **kwargs):
        return ''.join(random.choice(string.ascii_letters + string.digits) for i in range(random.randint(kwargs.get('min', 1), kwargs.get('max', 25))))

    def split(self, string, remove, offset=0):
        return string[len(f'{remove}') + offset:]

    def items(self, r, s):
        return [v for x in r for k, v in x.items() if k == s]

    def remove_duplicates(self, x: list):
        return list(dict.fromkeys(x))

    def search(self, find, data):
        return [x for x in data if find.lower() in str(x).lower()]

    def convert(self, text):
        return ''.join(i for i in text if ord(i) < 128)

    def remove(self, text):
        for x in trace.tracers:
            text = text.replace(str(x), '')
        return text

    def clean(self, text):  # Shorthand for self.convert and self.remove
        return self.convert(self.remove(text))

    def path(self, files):
        return os.path.join(os.path.dirname(os.path.abspath(files)))

    def abspath(self):
        return os.path.abspath('')

    def imports(self, fpath, folder='', ext='.py'):  # Get specific subfolder
        path = os.path.join(fpath, folder)
        return [self.split(os.path.join(root, name), self.abspath(), 1).replace('\\', '.')[:-len(ext)]
                for root, dirs, files in os.walk(path) for name in files
                if name.endswith(ext) and not name.endswith(f'__init__.py')]

    def scan(self, _file):  # Scan entire workspace for files
        return [self.split(os.path.join(root, name), self.abspath(), 1).replace('\\', '.')[:-3]
                for root, dirs, files in os.walk(self.abspath()) for name in files
                if name.endswith(_file)]


utils = Utils()
util = Utils()
utl = Utils()
