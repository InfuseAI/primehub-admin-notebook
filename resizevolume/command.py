#!/usr/bin/env python3
from subprocess import Popen, PIPE
import json


class Run(object):

    def __init__(self, command):
        self.commands = [
            Popen(command.split(' '), stdin=PIPE, stdout=PIPE, stderr=PIPE)]

    def pipe(self, command):
        proc = self.commands[-1]
        self.commands.append(
            Popen(command.split(' '), stdin=proc.stdout, stdout=PIPE, stderr=PIPE))
        return self

    def communicate(self):
        proc = self.commands[-1]
        stdout, stderr = proc.communicate()
        if stderr is not None:
            stderr = stderr.decode('utf8')
        return stdout.decode('utf8'), stderr

    def output(self):
        return self.communicate()[0]

    def json(self):
        stdout = self.communicate()[0]
        if stdout:
            return json.loads(stdout)
        return {}
