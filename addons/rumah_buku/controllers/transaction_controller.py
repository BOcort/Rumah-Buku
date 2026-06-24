from odoo import http
from odoo.http import request
import json

class TransactionController(http.Controller):
    @http.route('/api/transactions', type='http', auth='user', methods=['POST'], csrf=False)
    def create_transaction(self, **post):
        # Implementation for creating transaction via API
        # Expecting JSON payload: {"book_id": 1, "duration": 7}
        try:
            data = json.loads(request.httprequest.data)
            book_id = data.get('book_id')
            duration = data.get('duration', 7)
            
            transaction = request.env['rumah_buku.transaction_service'].create_borrow_transaction(
                request.env.user.id, book_id, duration
            )
            
            return request.make_response(json.dumps({'status': 'success', 'transaction_id': transaction.id, 'qr_token': transaction.qr_code_token}), headers=[('Content-Type', 'application/json')])
        except Exception as e:
            return request.make_response(json.dumps({'error': str(e)}), status=400, headers=[('Content-Type', 'application/json')])
