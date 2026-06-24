from odoo import http
from odoo.http import request
import json

class TransactionController(http.Controller):

    @http.route('/api/transactions', type='http', auth='user', methods=['GET'], csrf=False)
    def get_transactions(self, status='', page=1, limit=10, **kwargs):
        """API: Get list of transactions for current user."""
        user = request.env.user
        domain = [('user_id', '=', user.id)]

        if status:
            domain += [('status', '=', status)]

        Transaction = request.env['rumah_buku.transaction'].sudo()
        page = int(page)
        limit = int(limit)
        total = Transaction.search_count(domain)

        import math
        total_pages = max(1, math.ceil(total / limit))
        offset = (page - 1) * limit

        transactions = Transaction.search(domain, limit=limit, offset=offset, order='create_date desc')
        data = []
        for tx in transactions:
            data.append({
                'id': tx.id,
                'name': tx.name,
                'book_id': tx.book_id.id,
                'book_title': tx.book_id.name,
                'book_author': tx.book_id.author,
                'transaction_type': tx.transaction_type,
                'status': tx.status,
                'total_amount': tx.total_amount,
                'borrow_duration_days': tx.borrow_duration_days,
                'start_date': tx.start_date.isoformat() if tx.start_date else None,
                'due_date': tx.due_date.isoformat() if tx.due_date else None,
                'returned_date': tx.returned_date.isoformat() if tx.returned_date else None,
                'is_overdue': tx.is_overdue,
                'qr_code_token': tx.qr_code_token,
                'cover_url': tx.book_id.cover_display_url,
            })

        result = {
            'status': 'success',
            'data': data,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': total_pages,
            }
        }
        return request.make_response(
            json.dumps(result),
            headers=[('Content-Type', 'application/json')]
        )

    @http.route('/api/transactions/<int:transaction_id>', type='http', auth='user', methods=['GET'], csrf=False)
    def get_transaction_detail(self, transaction_id, **kwargs):
        """API: Get single transaction detail."""
        tx = request.env['rumah_buku.transaction'].sudo().browse(transaction_id)
        if not tx.exists() or tx.user_id.id != request.env.user.id:
            response = request.make_response(
                json.dumps({'error': 'Transaction not found'}),
                headers=[('Content-Type', 'application/json')]
            )
            response.status_code = 404
            return response

        data = {
            'id': tx.id,
            'name': tx.name,
            'book_id': tx.book_id.id,
            'book_title': tx.book_id.name,
            'book_author': tx.book_id.author,
            'transaction_type': tx.transaction_type,
            'status': tx.status,
            'total_amount': tx.total_amount,
            'borrow_duration_days': tx.borrow_duration_days,
            'start_date': tx.start_date.isoformat() if tx.start_date else None,
            'due_date': tx.due_date.isoformat() if tx.due_date else None,
            'returned_date': tx.returned_date.isoformat() if tx.returned_date else None,
            'is_overdue': tx.is_overdue,
            'qr_code_token': tx.qr_code_token,
            'cover_url': tx.book_id.cover_display_url,
            'notes': tx.notes,
            'pickup_date': tx.pickup_date.isoformat() if tx.pickup_date else None,
            'pickup_time': tx.pickup_time,
        }
        return request.make_response(
            json.dumps({'status': 'success', 'data': data}),
            headers=[('Content-Type', 'application/json')]
        )

    @http.route('/api/transactions', type='http', auth='user', methods=['POST'], csrf=False)
    def create_transaction(self, **post):
        """API: Create a new borrow transaction."""
        # Expecting JSON payload: {"book_id": 1, "duration": 7}
        try:
            raw_data = request.httprequest.get_data(as_text=True)
            if not raw_data:
                response = request.make_response(
                    json.dumps({'error': 'Request body is empty. Send JSON payload.'}),
                    headers=[('Content-Type', 'application/json')]
                )
                response.status_code = 400
                return response

            data = json.loads(raw_data)
            book_id = data.get('book_id')
            duration = data.get('duration', 7)
            
            transaction = request.env['rumah_buku.transaction_service'].create_borrow_transaction(
                request.env.user.id, book_id, duration
            )
            
            return request.make_response(
                json.dumps({
                    'status': 'success',
                    'transaction_id': transaction.id,
                    'qr_token': transaction.qr_code_token,
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
