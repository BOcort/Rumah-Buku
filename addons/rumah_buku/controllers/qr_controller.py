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
            return request.make_response(
                json.dumps({'error': 'Transaction not found'}),
                status=404,
                headers=[('Content-Type', 'application/json')]
            )

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
            data = json.loads(request.httprequest.data)
            token = data.get('token', '').strip()

            if not token:
                return request.make_response(
                    json.dumps({'error': 'Token is required'}),
                    status=400,
                    headers=[('Content-Type', 'application/json')]
                )

            # Find transactions with this token
            transactions = request.env['rumah_buku.transaction'].sudo().search([
                ('qr_code_token', '=', token),
            ])

            if not transactions:
                return request.make_response(
                    json.dumps({'error': 'Token QR tidak ditemukan'}),
                    status=404,
                    headers=[('Content-Type', 'application/json')]
                )

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
            return request.make_response(
                json.dumps({'error': str(e)}),
                status=400,
                headers=[('Content-Type', 'application/json')]
            )

    @http.route('/api/qr/confirm-pickup', type='http', auth='user',
                methods=['POST'], csrf=False)
    def confirm_pickup(self, **kwargs):
        """Admin confirms pickup — changes status to 'borrowed', sets dates."""
        try:
            data = json.loads(request.httprequest.data)
            token = data.get('token', '').strip()

            if not token:
                return request.make_response(
                    json.dumps({'error': 'Token is required'}),
                    status=400,
                    headers=[('Content-Type', 'application/json')]
                )

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
            return request.make_response(
                json.dumps({'error': str(e)}),
                status=400,
                headers=[('Content-Type', 'application/json')]
            )
