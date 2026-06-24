from odoo import models, fields


class Membership(models.Model):
    _name = 'rumah_buku.membership'
    _description = 'Keanggotaan Bulanan Rumah Buku'
    _rec_name = 'user_id'
    _order = 'create_date desc'

    user_id = fields.Many2one('res.users', string='Member', required=True)
    plan = fields.Selection([
        ('basic', 'Basic'),
        ('premium', 'Premium'),
    ], string='Plan', default='basic', required=True)
    monthly_fee = fields.Float(
        string='Monthly Fee (Rp)',
        digits=(12, 0),
        default=50000,
        help='Biaya keanggotaan per bulan'
    )
    status = fields.Selection([
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='active')
    start_date = fields.Date(string='Start Date', default=fields.Date.today)
    expiry_date = fields.Date(string='Expiry Date')
    auto_renew = fields.Boolean(string='Auto Renew', default=True)
