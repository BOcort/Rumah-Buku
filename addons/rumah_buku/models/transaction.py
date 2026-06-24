from odoo import models, fields, api
from datetime import timedelta


class Transaction(models.Model):
    _name = 'rumah_buku.transaction'
    _description = 'Transaksi Peminjaman atau Pembelian Buku'
    _rec_name = 'name'
    _order = 'create_date desc'

    name = fields.Char(
        string='Transaction Number',
        required=True, copy=False, readonly=True,
        default='New'
    )
    user_id = fields.Many2one('res.users', string='User', required=True)
    book_id = fields.Many2one('rumah_buku.book', string='Book', required=True)
    transaction_type = fields.Selection([
        ('borrow', 'Borrow'),
        ('buy', 'Buy'),
    ], string='Type', required=True)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('ready_for_pickup', 'Ready for Pickup'),
        ('borrowed', 'Borrowed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='pending')

    qr_code_token = fields.Char(string='QR Code Token', copy=False)
    borrow_duration_days = fields.Integer(
        string='Borrow Duration (Days)',
        default=10,
        help='Batas peminjaman default 10 hari, lebih dari itu kena denda'
    )
    start_date = fields.Datetime(string='Start Date')
    due_date = fields.Datetime(string='Due Date')
    returned_date = fields.Datetime(string='Returned Date')
    notes = fields.Text(string='Notes')

    # Pickup scheduling
    pickup_date = fields.Date(string='Pickup Date')
    pickup_time = fields.Char(string='Pickup Time Slot')

    # Computed: total amount
    total_amount = fields.Float(
        string='Total Amount (Rp)',
        compute='_compute_total_amount',
        store=True,
        digits=(12, 0)
    )

    # Computed: is overdue
    is_overdue = fields.Boolean(
        string='Is Overdue',
        compute='_compute_is_overdue',
        store=False
    )

    # Relations
    payment_ids = fields.One2many(
        'rumah_buku.payment', 'transaction_id', string='Payments'
    )
    fine_ids = fields.One2many(
        'rumah_buku.fine', 'transaction_id', string='Fines'
    )

    @api.depends('transaction_type', 'book_id.sell_price',
                 'book_id.rent_price_per_day', 'borrow_duration_days')
    def _compute_total_amount(self):
        for tx in self:
            if tx.transaction_type == 'buy' and tx.book_id:
                tx.total_amount = tx.book_id.sell_price or 0
            elif tx.transaction_type == 'borrow' and tx.book_id:
                price_per_day = tx.book_id.rent_price_per_day or 0
                duration = tx.borrow_duration_days or 10
                tx.total_amount = price_per_day * duration
            else:
                tx.total_amount = 0

    @api.depends('due_date', 'status')
    def _compute_is_overdue(self):
        now = fields.Datetime.now()
        for tx in self:
            if tx.status == 'borrowed' and tx.due_date:
                tx.is_overdue = now > tx.due_date
            else:
                tx.is_overdue = False

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'rumah_buku.transaction'
            ) or 'New'
        return super(Transaction, self).create(vals)
