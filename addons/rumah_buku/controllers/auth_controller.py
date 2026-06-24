from odoo import http, _
from odoo.http import request
from odoo.addons.web.controllers.home import Home
import werkzeug

class AuthController(Home):
    @http.route('/web/login', type='http', auth="none", s2s=False, csrf=False)
    def web_login(self, redirect=None, **kw):
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return request.redirect(redirect)

        if not request.uid:
            request.update_env(user=request.env.ref('base.public_user').id)

        values = {
            'error': "",
            'redirect': redirect,
        }

        if request.httprequest.method == 'POST':
            old_uid = request.uid
            try:
                uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
                request.params['login_success'] = True
                return request.redirect(self._login_redirect(uid, redirect=redirect))
            except Exception as e:
                values['error'] = _("Wrong login/password")
                
        return request.render('rumah_buku.frontend_login', values)
        
    @http.route('/web/signup', type='http', auth='public', website=True, s2s=False, csrf=False)
    def web_signup(self, *args, **kw):
        values = {'error': ''}
        if request.httprequest.method == 'POST':
            try:
                # Basic signup implementation
                name = kw.get('name')
                login = kw.get('login')
                password = kw.get('password')
                confirm_password = kw.get('confirm_password')
                
                if password != confirm_password:
                    values['error'] = _("Passwords do not match.")
                    return request.render('rumah_buku.frontend_register', values)
                
                request.env['res.users'].sudo().create({
                    'name': name,
                    'login': login,
                    'password': password,
                    'groups_id': [(6, 0, [request.env.ref('base.group_portal').id])]
                })
                # Authenticate after signup
                request.session.authenticate(request.session.db, login, password)
                return request.redirect('/catalog')
            except Exception as e:
                values['error'] = str(e)
                
        return request.render('rumah_buku.frontend_register', values)
