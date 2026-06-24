from odoo import models, fields

class Fine(models.Model):
    _name = 'rumah_buku.fine'
    _description = 'Denda Keterlambatan atau Kerusakan'

    transaction_id = fields.Many2one('rumah_buku.transaction', string='Transaction', required=True)
    user_id = fields.Many2one('res.users', string='User', required=True)
    amount = fields.Float(string='Amount', required=True)
    reason = fields.Selection([
        ('late_return', 'Late Return'),
        ('damaged', 'Damaged'),
        ('lost', 'Lost')
    ], string='Reason', default='late_return')
    status = fields.Selection([
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid')
    ], string='Status', default='unpaid')
