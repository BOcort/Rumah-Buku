from odoo import models, fields, api


class Book(models.Model):
    _name = 'rumah_buku.book'
    _description = 'Buku di Rumah Buku'
    _rec_name = 'name'
    _order = 'create_date desc'

    name = fields.Char(string='Title', required=True)
    isbn = fields.Char(string='ISBN')
    author = fields.Char(string='Author', required=True)
    publisher = fields.Char(string='Publisher')
    synopsis = fields.Text(string='Synopsis')
    cover_url = fields.Char(string='Cover URL')
    cover_image = fields.Binary(string='Cover Image', attachment=True)
    category = fields.Selection([
        ('fiction', 'Fiction'),
        ('non_fiction', 'Non-Fiction'),
        ('tech_business', 'Tech & Business'),
        ('science', 'Science'),
        ('history', 'History'),
        ('art_design', 'Art & Design'),
        ('self_help', 'Self Help'),
        ('other', 'Other'),
    ], string='Category', default='other')
    status = fields.Selection([
        ('available', 'Available'),
        ('borrowed', 'Borrowed'),
        ('sold', 'Sold'),
    ], string='Status', default='available')
    stock = fields.Integer(string='Stock', default=1)
    location_rack = fields.Char(string='Location Rack')
    sell_price = fields.Float(string='Sell Price (Rp)', digits=(12, 0))
    rent_price_per_day = fields.Float(
        string='Rent Price per Day (Rp)',
        digits=(12, 0),
        default=5000,
        help='Harga sewa per hari dalam Rupiah'
    )
    is_rentable = fields.Boolean(string='Is Rentable', default=True)
    publication_year = fields.Char(string='Publication Year')
    pages = fields.Integer(string='Pages')

    # Computed: cover display URL
    cover_display_url = fields.Char(
        string='Cover Display URL',
        compute='_compute_cover_display_url',
        store=False
    )

    @api.depends('cover_image', 'cover_url')
    def _compute_cover_display_url(self):
        for book in self:
            if book.cover_image:
                book.cover_display_url = f'/web/image/rumah_buku.book/{book.id}/cover_image'
            elif book.cover_url:
                book.cover_display_url = book.cover_url
            else:
                book.cover_display_url = '/rumah_buku/static/src/img/no_cover.png'

    @api.model
    def get_category_label(self, key):
        """Get human-readable category label from selection key."""
        selection = dict(self._fields['category'].selection)
        return selection.get(key, key or '-')
