#!/usr/bin/python
# -*- coding: utf-8 -*-
# rdiffweb, A web interface to rdiff-backup repositories
# Copyright (C) 2014 rdiffweb contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import
from __future__ import unicode_literals

import cherrypy
import logging

from rdiffweb import librdiff
from rdiffweb import page_main
from rdiffweb.rdw_helpers import unquote_url


# Define the logger
logger = logging.getLogger(__name__)


class HistoryPage(page_main.MainPage):

    def _cp_dispatch(self, vpath):
        """Used to handle permalink URL.
        ref http://cherrypy.readthedocs.org/en/latest/advanced.html"""
        # Notice vpath contains bytes.
        if len(vpath) > 0:
            # /the/full/path/
            path = []
            while len(vpath) > 0:
                path.append(unquote_url(vpath.pop(0)))
            cherrypy.request.params['path'] = b"/".join(path)
            return self

        return vpath

    @cherrypy.expose
    def index(self, path=b""):
        assert isinstance(path, bytes)

        logger.debug("history [%r]", path)

        repo_obj = self.validate_user_path(path)[0]
        assert isinstance(repo_obj, librdiff.RdiffRepo)

        parms = {
            "repo_name": repo_obj.display_name,
            "repo_path": repo_obj.path,
            "history_entries": repo_obj.get_history_entries()
        }

        return self._compile_template("history.html", **parms)
