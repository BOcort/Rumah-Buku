from odoo import http, _
from odoo.http import request
from odoo.addons.web.controllers.home import Home
import werkzeug
import json


class AuthController(http.Controller):

    # ─── Custom Web Login & Signup (Separate from native Odoo) ───────────────
    @http.route('/app/login', type='http', auth="public", website=True, csrf=False)
    def app_login(self, **kw):
        # If already logged in, show success page directly
        if request.session.uid and request.env.user.login != 'public':
            return request.render('rumah_buku.frontend_login_success', {'name': request.env.user.name})

        values = {'error': ""}
        
        if request.httprequest.method == 'POST':
            login = kw.get('login')
            password = kw.get('password')
            try:
                # Authenticate
                uid = request.env['res.users'].authenticate(request.session.db, login, password, None)
                if uid:
                    request.session.uid = uid
                    request.session.login = login
                    request.session.session_token = uid
                    user = request.env['res.users'].sudo().browse(uid)
                    # Show the 5-second countdown page instead of instant redirect
                    return request.render('rumah_buku.frontend_login_success', {'name': user.name})
                else:
                    values['error'] = _("Wrong login/password")
            except Exception as e:
                values['error'] = _("Wrong login/password")
                
        return request.render('rumah_buku.frontend_login', values)
        
    @http.route('/app/signup', type='http', auth='public', website=True, csrf=False)
    def app_signup(self, **kw):
        values = {'error': ''}
        if request.httprequest.method == 'POST':
            try:
                name = kw.get('name')
                login = kw.get('login')
                password = kw.get('password')
                confirm_password = kw.get('confirm_password')
                
                if password != confirm_password:
                    values['error'] = _("Passwords do not match.")
                    return request.render('rumah_buku.frontend_register', values)
                
                # Create user
                request.env['res.users'].sudo().create({
                    'name': name,
                    'login': login,
                    'password': password,
                    'share': True
                })
                
                # Authenticate and show success page
                uid = request.env['res.users'].authenticate(request.session.db, login, password, None)
                if uid:
                    request.session.uid = uid
                    request.session.login = login
                    request.session.session_token = uid
                    return request.render('rumah_buku.frontend_login_success', {'name': name})
            except Exception as e:
                values['error'] = str(e)
                
        return request.render('rumah_buku.frontend_register', values)

    # ─── JSON API Login (for Postman / external clients) ─────────────────────
    @http.route('/api/auth/login', type='http', auth='none', methods=['POST'], csrf=False)
    def api_login(self, **kwargs):
        """
        JSON API login endpoint for Postman / REST clients.
        Body: {"db": "odoo_development", "login": "admin@email.com", "password": "admin#123"}
        Returns session_id cookie + user info.
        """
        try:
            raw_data = request.httprequest.get_data(as_text=True)
            if not raw_data:
                response = request.make_response(
                    json.dumps({'error': 'Request body is empty. Send JSON with db, login, password.'}),
                    headers=[('Content-Type', 'application/json')]
                )
                response.status_code = 400
                return response

            data = json.loads(raw_data)
            db = data.get('db', 'odoo_development')
            login = data.get('login', '')
            password = data.get('password', '')

            if not login or not password:
                response = request.make_response(
                    json.dumps({'error': 'login and password are required'}),
                    headers=[('Content-Type', 'application/json')]
                )
                response.status_code = 400
                return response

            # Use direct model authentication
            uid = request.env['res.users'].authenticate(db, login, password, None)
            
            if not uid:
                response = request.make_response(
                    json.dumps({'error': 'Invalid credentials'}),
                    headers=[('Content-Type', 'application/json')]
                )
                response.status_code = 401
                return response
                
            # Manually set up session for API
            request.session.db = db
            request.session.uid = uid
            request.session.login = login
            request.session.session_token = uid


            user = request.env['res.users'].sudo().browse(uid)
            result = {
                'status': 'success',
                'uid': uid,
                'session_id': request.session.sid,
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'login': user.login,
                    'is_admin': user.has_group('base.group_system'),
                },
            }
            return request.make_response(
                json.dumps(result),
                headers=[('Content-Type', 'application/json')]
            )

        except Exception as e:
            response = request.make_response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')]
            )
            response.status_code = 400
            return response

    @http.route('/api/auth/logout', type='http', auth='user', methods=['POST'], csrf=False)
    def api_logout(self, **kwargs):
        """JSON API logout."""
        request.session.logout(keep_db=True)
        return request.make_response(
            json.dumps({'status': 'success', 'message': 'Logged out'}),
            headers=[('Content-Type', 'application/json')]
        )

    @http.route('/api/auth/me', type='http', auth='user', methods=['GET'], csrf=False)
    def api_me(self, **kwargs):
        """Get current session user info."""
        user = request.env.user
        result = {
            'status': 'success',
            'user': {
                'id': user.id,
                'name': user.name,
                'login': user.login,
                'is_admin': user.has_group('base.group_system'),
                'phone_number': user.phone_number if hasattr(user, 'phone_number') else '',
                'role': user.role if hasattr(user, 'role') else 'user',
                'is_suspended': user.is_suspended if hasattr(user, 'is_suspended') else False,
            }
        }
        return request.make_response(
            json.dumps(result),
            headers=[('Content-Type', 'application/json')]
        )
