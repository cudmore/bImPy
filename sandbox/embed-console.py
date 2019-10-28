# -*- coding: utf-8 -*-
#/usr/bin/python
from gevent import monkey; monkey.patch_all()

import gevent
import sys

from pyqtconsole.qt.QtWidgets import QApplication
from pyqtconsole.console import PythonConsole


def greet():
    print("hello world")


if __name__ == '__main__':
    app = QApplication([])

    console = PythonConsole()
    console.push_local_ns('greet', greet)
    console.show()

    console.eval_executor(gevent.spawn)

    sys.exit(app.exec_())