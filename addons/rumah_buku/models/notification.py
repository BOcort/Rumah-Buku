from odoo import models, fields

class Notification(models.Model):
    _name = 'rumah_buku.notification'
    _description = 'Notifikasi Pengguna'

    user_id = fields.Many2one('res.users', string='User', required=True)
    title = fields.Char(string='Title', required=True)
    message = fields.Text(string='Message', required=True)
    notification_type = fields.Selection([
        ('order_update', 'Order Update'),
        ('fine_alert', 'Fine Alert'),
        ('system', 'System')
    ], string='Type')
    is_read = fields.Boolean(string='Is Read', default=False)
