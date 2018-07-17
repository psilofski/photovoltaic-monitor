from distutils.core import setup
import py2exe
import matplotlib


dll_excludes = ['msvcp90.dll',
                'libgdk-win32-2.0-0.dll',
                'libgobject-2.0-0.dll'
                ]

excludes = ['_gtkagg',
            'wxagg',
            '_agg2',
            '_cairo',
            '_cocoaagg',
            '_fltkagg',
            '_gtk',
            '_gtkcairo',
            ]

setup(
    console=['run.py'],
    data_files=matplotlib.get_py2exe_datafiles(),
    options = {"py2exe": {"dll_excludes": dll_excludes,
                          'excludes': excludes,
                          "includes" : ["matplotlib.backends.backend_tkagg"],
                          }
               }
    )
