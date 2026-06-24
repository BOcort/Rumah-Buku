from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    # Supabase Auth ID equivalent can just be stored as a char if needed,
    # or Odoo's default login/id is used. We'll add custom fields from ERD.
    phone_number = fields.Char(string='Phone Number')
    role = fields.Selection([
        ('user', 'User'),
        ('admin', 'Admin'),
        ('superadmin', 'Superadmin')
    ], string='Role', default='user')
    avatar_url = fields.Char(string='Avatar URL')
    is_suspended = fields.Boolean(string='Is Suspended', default=False)
