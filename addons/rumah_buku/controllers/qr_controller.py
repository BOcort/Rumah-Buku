from odoo import http
from odoo.http import request
import json
import io
import base64

try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False


class QRController(http.Controller):

    @http.route('/api/qr/generate/<int:transaction_id>', type='http',
                auth='user', methods=['GET'], csrf=False)
    def generate_qr(self, transaction_id, **kwargs):
        """Generate QR code image for a transaction."""
        tx = request.env['rumah_buku.transaction'].sudo().browse(transaction_id)
        if not tx.exists():
            response = request.make_response(
                json.dumps({'error': 'Transaction not found'}),
                headers=[('Content-Type', 'application/json')]
            )
            response.status_code = 404
            return response

        token = tx.qr_code_token or 'no-token'

        if HAS_QRCODE:
            # Generate QR using python qrcode library
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(token)
            qr.make(fit=True)
            img = qr.make_image(fill_color='#1a3a3a', back_color='white')

            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)

            return request.make_response(
                buffer.read(),
                headers=[
                    ('Content-Type', 'image/png'),
                    ('Cache-Control', 'no-cache'),
                ]
            )
        else:
            # Fallback: redirect to external QR API
            qr_url = f'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={token}'
            return request.redirect(qr_url)

    @http.route('/api/qr/verify', type='http', auth='user',
                methods=['POST'], csrf=False)
    def verify_qr(self, **kwargs):
        """Admin verifies QR token — confirms book pickup."""
        try:
            raw_data = request.httprequest.get_data(as_text=True)
            data = json.loads(raw_data) if raw_data else {}
            token = data.get('token', '').strip()

            if not token:
                response = request.make_response(
                    json.dumps({'error': 'Token is required'}),
                    headers=[('Content-Type', 'application/json')]
                )
                response.status_code = 400
                return response

            # Find transactions with this token or book name
            domain = [
                ('status', 'in', ['ready_for_pickup', 'borrowed']),
                '|', ('qr_code_token', '=', token), ('book_id.name', 'ilike', token)
            ]
            transactions = request.env['rumah_buku.transaction'].sudo().search(domain, order='create_date desc', limit=1)

            if not transactions:
                response = request.make_response(
                    json.dumps({'error': 'Token QR atau Buku tidak ditemukan (Atau belum siap dipickup)'}),
                    headers=[('Content-Type', 'application/json')]
                )
                response.status_code = 404
                return response

            # Get transaction details
            tx = transactions[0]
            result = {
                'status': 'success',
                'transaction': {
                    'id': tx.id,
                    'name': tx.name,
                    'book_title': tx.book_id.name,
                    'book_author': tx.book_id.author,
                    'user_name': tx.user_id.name,
                    'user_email': tx.user_id.login,
                    'type': tx.transaction_type,
                    'current_status': tx.status,
                    'total_amount': tx.total_amount,
                    'borrow_duration': tx.borrow_duration_days,
                    'cover_url': tx.book_id.cover_display_url,
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

    @http.route('/api/qr/confirm-pickup', type='http', auth='user',
                methods=['POST'], csrf=False)
    def confirm_pickup(self, **kwargs):
        """Admin confirms pickup — changes status to 'borrowed', sets dates."""
        try:
            raw_data = request.httprequest.get_data(as_text=True)
            data = json.loads(raw_data) if raw_data else {}
            token = data.get('token', '').strip()

            if not token:
                response = request.make_response(
                    json.dumps({'error': 'Token is required'}),
                    headers=[('Content-Type', 'application/json')]
                )
                response.status_code = 400
                return response

            service = request.env['rumah_buku.transaction_service'].sudo()
            transaction = service.confirm_pickup(token)

            return request.make_response(
                json.dumps({
                    'status': 'success',
                    'message': f'Buku "{transaction.book_id.name}" berhasil diserahkan ke {transaction.user_id.name}.',
                    'transaction_id': transaction.id,
                    'due_date': transaction.due_date.strftime('%d %b %Y') if transaction.due_date else '',
                }),
                headers=[('Content-Type', 'application/json')]
            )

        except Exception as e:
            response = request.make_response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')]
            )
            response.status_code = 400
            return response
