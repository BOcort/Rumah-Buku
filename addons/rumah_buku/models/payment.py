from odoo import models, fields

class Payment(models.Model):
    _name = 'rumah_buku.payment'
    _description = 'Data Pembayaran'

    transaction_id = fields.Many2one('rumah_buku.transaction', string='Transaction', required=True)
    user_id = fields.Many2one('res.users', string='User', required=True)
    midtrans_order_id = fields.Char(string='Midtrans Order ID', copy=False)
    gross_amount = fields.Float(string='Gross Amount', required=True)
    payment_type = fields.Char(string='Payment Type')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('settlement', 'Settlement'),
        ('expire', 'Expire'),
        ('cancel', 'Cancel')
    ], string='Status', default='pending')
    paid_at = fields.Datetime(string='Paid At')
