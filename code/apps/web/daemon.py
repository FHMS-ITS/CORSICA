#!/usr/bin/env python3
# Python webcrawler using wget
# Used to collect accessible files for a given IP
# Variable starting point for crawling (defaults to /)
# Follow links, image tags, style directives as long as they stay on the same web page

import os

from utils.docker import build_docker
from utils.log import _info


def run(config):
    _info("corsica.web", "Daemon started")

    build_docker("corsica-web", os.path.dirname(os.path.realpath(__file__)))
