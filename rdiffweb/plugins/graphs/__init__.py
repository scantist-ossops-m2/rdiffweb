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
"""
LDAP UserDB backend used to validate credentials. This plugin will
use SQLite database for user's data. Both, LDAP and SQLite plugin must be
enabled.

The LDAP plugin cannot create new users. Users must already exist in the
LDAP directory. It would be difficult to create a new LDAP user, as the
creation of a LDAP user requires properties which are not made available
to the LDAP plugin.
"""
# Define the logger

from __future__ import absolute_import
from __future__ import unicode_literals

from builtins import bytes
from builtins import str
import cherrypy
from future.utils import iteritems
import logging

from rdiffweb import librdiff, rdw_helpers
from rdiffweb import page_main
from rdiffweb.i18n import ugettext as _
from rdiffweb.rdw_helpers import unquote_url
from rdiffweb.rdw_plugin import IRdiffwebPlugin, ITemplateFilterPlugin


_logger = logging.getLogger(__name__)


def url_for_graphs(repo, graph=''):
    """
    Build a URL to display graphs for the given repo.
    """
    assert isinstance(repo, bytes)
    url = []
    url.append("/graphs/%s/" % (graph))
    if repo:
        repo = repo.rstrip(b"/")
        url.append(rdw_helpers.quote_url(repo))
        url.append("/")
    return ''.join(url)


class GraphsPage(page_main.MainPage):

    def _cp_dispatch(self, vpath):
        """
        Used to handle permalink URL.
        /graphs/*/repo_path
        """
        assert len(vpath) > 0

        # First vpath, is the graphs
        graph = unquote_url(vpath.pop(0))

        # Extract the repo path
        path = []
        while len(vpath) > 0:
            path.append(unquote_url(vpath.pop(0)))
        cherrypy.request.params['graph'] = graph.decode('ascii')
        cherrypy.request.params['path'] = b"/".join(path)
        return self

    def _data(self, path, **kwargs):
        assert isinstance(path, bytes)

        _logger.debug("repo stats [%r]", path)

        # Check user permissions
        try:
            repo_obj = self.validate_user_path(path)[0]
        except librdiff.FileError as e:
            _logger.exception("invalid user path [%r]", path)
            return self._compile_error_template(str(e))

        attrs = [
            'starttime', 'endtime', 'elapsedtime', 'sourcefiles', 'sourcefilesize',
            'mirrorfiles', 'mirrorfilesize', 'newfiles', 'newfilesize', 'deletedfiles',
            'deletedfilesize', 'changedfiles', 'changedsourcesize', 'changedmirrorsize',
            'incrementfiles', 'incrementfilesize', 'totaldestinationsizechange', 'errors']

        # Return a generator
        def func():
            # Header
            yield 'date'
            for attr in attrs:
                yield ','
                yield attr
            yield '\n'
            # Content
            for d, s in iteritems(repo_obj.session_statistics):
                yield str(d.getSeconds())
                for attr in attrs:
                    yield ','
                    yield str(getattr(s, attr))
                yield '\n'

        return func()

    def _page(self, path, graph, **kwargs):
        """
        Generic method to show graphs.
        """
        assert isinstance(path, bytes)
        assert isinstance(graph, str)

        _logger.debug("repo graphs [%s][%r]", graph, path)

        # Check user permissions
        try:
            repo_obj = self.validate_user_path(path)[0]
        except librdiff.FileError as e:
            _logger.exception("invalid user path [%r]", path)
            return self._compile_error_template(str(e))

        # Check if any action to process.
        params = {
            'repo_name': repo_obj.display_name,
            'repo_path': repo_obj.path,
            'graphs': graph,
        }

        # Generate page.
        return self._compile_template("graphs_%s.html" % graph, **params)

    @cherrypy.expose
    def index(self, path, graph, **kwargs):
        """
        Called to show every graphs
        """
        # check if data should be shown.
        if graph == 'data':
            return self._data(path, **kwargs)

        # Else, show graph.
        return self._page(path, graph, **kwargs)


class GraphsPlugins(ITemplateFilterPlugin):
    """
    Plugin to display repository graphs.
    """

    def activate(self):
        # Register new handler to show graphs.
        self.app.root.graphs = GraphsPage(self.app)
        # Register function into templates
        self.app.templates.jinja_env.globals['url_for_graphs'] = url_for_graphs
        # Call original
        IRdiffwebPlugin.activate(self)

    def filter_data(self, template_name, data):

        if data.get('repo_path'):
            # Add our graph item in repo_nav_bar
            # id, label, url, icon
            data.setdefault('repo_nav_bar_extras', []).append(('graphs', _('Graphs'), url_for_graphs(data.get('repo_path'), 'activities'), 'icon-chart-bar'))