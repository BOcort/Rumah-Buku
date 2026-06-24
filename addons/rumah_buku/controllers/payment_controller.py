from odoo import http
from odoo.http import request
import json

class PaymentController(http.Controller):
    @http.route('/api/payments/webhook', type='http', auth='public', methods=['POST'], csrf=False)
    def midtrans_webhook(self, **post):
        # Basic skeleton for Midtrans webhook
        try:
            data = json.loads(request.httprequest.data)
            order_id = data.get('order_id')
            transaction_status = data.get('transaction_status')
            
            payment = request.env['rumah_buku.payment'].sudo().search([('midtrans_order_id', '=', order_id)], limit=1)
            if payment:
                if transaction_status in ['settlement', 'capture']:
                    payment.status = 'settlement'
                elif transaction_status in ['cancel', 'deny', 'expire']:
                    payment.status = 'cancel'
                    
            return request.make_response(json.dumps({'status': 'ok'}), headers=[('Content-Type', 'application/json')])
        except Exception as e:
            return request.make_response(json.dumps({'error': str(e)}), status=400, headers=[('Content-Type', 'application/json')])
