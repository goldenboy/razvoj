###############################################################################
#
#  Copyright (C) 2007-TODAY OpenERP SA. All Rights Reserved.
#
#  $Id$
#
#  Developed by OpenERP (http://openerp.com) and Axelor (http://axelor.com).
#
#  The OpenERP web client is distributed under the "OpenERP Public License".
#  It's based on Mozilla Public License Version (MPL) 1.1 with following 
#  restrictions:
#
#  -   All names, links and logos of OpenERP must be kept as in original
#      distribution without any changes in all software screens, especially
#      in start-up page and the software header, even if the application
#      source code has been changed or updated or code has been added.
#
#  You can see the MPL licence at: http://www.mozilla.org/MPL/MPL-1.1.html
#
###############################################################################
import urlparse

import cherrypy

from openobject import tools, rpc
from openobject.tools import expose
import openobject


__all__ = ["secured", "unsecured", "login"]


@expose(template="/openerp/controllers/templates/login.mako")
def login(target, db=None, user=None, password=None, action=None, message=None, origArgs={}):

    url = rpc.get_session().connection_string
    url = str(url[:-1])

    dblist = []
    try:
        dblist = rpc.get_session().listdb()
    except:
        message = _("Could not connect to server")

    dbfilter = cherrypy.request.app.config['openerp-web'].get('dblist.filter')
    if dbfilter:
        base, _ = urlparse.urlsplit(cherrypy.request.base)\
                    .hostname.split('.', 1)

        if dbfilter == 'EXACT':
            if dblist is None:
                db = base
                dblist = [db]
            else:
                dblist = [d for d in dblist if d == base]

        elif dbfilter == 'UNDERSCORE':
            if dblist is None:
                if db and not db.startswith(base + '_'):
                    db = None
            else:
                dblist = [d for d in dblist if d.startswith(base + '_')]

        elif dbfilter == 'BOTH':
            if dblist is None:
                if db and db != base and not db.startswith(base + '_'):
                    db = None
            else:
                dblist = [d for d in dblist if d.startswith(base + '_') or d == base]

    info = None
    try:
        info = rpc.get_session().execute_noauth('common', 'login_message') or ''
    except:
        pass
    return dict(target=target, url=url, dblist=dblist, db=db, user=user, password=password,
            action=action, message=message, origArgs=origArgs, info=info)

def secured(fn):
    """A Decorator to make a SecuredController controller method secured.
    """
    def clear_login_fields(kw):

        if not kw.get('login_action'):
            return

        for k in ('db', 'user', 'password'):
            kw.pop(k, None)
        for k in kw.keys():
            if k.startswith('login_'):
                del kw[k]

    def get_orig_args(kw):
        if not kw.get('login_action'):
            return kw

        new_kw = kw.copy()
        clear_login_fields(new_kw)
        return new_kw

    def wrapper(*args, **kw):
        """The wrapper function to secure exposed methods
        """

        if rpc.get_session().is_logged() and kw.get('login_action') != 'login':
            # User is logged in; allow access
            clear_login_fields(kw)
            return fn(*args, **kw)
        else:
            action = kw.get('login_action', '')
            # get some settings from cookies
            try:
                db = cherrypy.request.cookie['terp_db'].value
                user = cherrypy.request.cookie['terp_user'].value
            except:
                db = ''
                user = ''

            db = kw.get('db', db)
            user = ustr(kw.get('user', user))
            password = kw.get('password', '')

            # See if the user just tried to log in
            if rpc.get_session().login(db, user, password) <= 0:
                # Bad login attempt
                if action == 'login':
                    message = _("Bad username or password")
                    return login(cherrypy.request.path_info, message=message,
                        db=db, user=user, action=action, origArgs=get_orig_args(kw))
                else:
                    message = ''

                kwargs = {}
                if action: kwargs['action'] = action
                if message: kwargs['message'] = message
                base = cherrypy.request.path_info
                if cherrypy.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    cherrypy.response.status = 401
                    next_key = 'next'
                else:
                    cherrypy.response.status = 303
                    next_key = 'location' # login?location is the redirection destination w/o next

                if base and base != '/' and cherrypy.request.method == 'GET':
                    kwargs[next_key] = "%s?%s" % (base, cherrypy.request.query_string)

                login_url = openobject.tools.url(
                    '/openerp/login', db=db, user=user, **kwargs
                )
                cherrypy.response.headers['Location'] = login_url
                return """
                    <html>
                        <head>
                            <script type="text/javascript">
                                window.location.href="%s"
                            </script>
                        </head>
                        <body>
                        </body>
                    </html>
                """%(login_url)

            # Authorized. Set db, user name in cookies
            cookie = cherrypy.response.cookie
            cookie['terp_db'] = db
            cookie['terp_user'] = user.encode('utf-8')
            cookie['terp_db']['max-age'] = 3600
            cookie['terp_user']['max-age'] = 3600
            cookie['terp_db']['path'] = '/'
            cookie['terp_user']['path'] = '/'

            # User is now logged in, so show the content
            clear_login_fields(kw)
            return fn(*args, **kw)

    return tools.decorated(wrapper, fn, secured=True)


def unsecured(fn):
    """A Decorator to make a SecuredController controller method unsecured.
    """

    def wrapper(*args, **kw):
        return fn(*args, **kw)

    return tools.decorated(wrapper, fn, secured=False)


# vim: ts=4 sts=4 sw=4 si et
