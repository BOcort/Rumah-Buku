from odoo import http
from odoo.http import request
import math


class FrontendController(http.Controller):

    BOOKS_PER_PAGE = 12

    @http.route(['/', '/catalog'], type='http', auth='public', website=True)
    def catalog(self, search='', category='', status_filter='', sort='newest', page=1, **kwargs):
        """Book catalog with search, filter, sort, and pagination."""
        domain = []

        # Search
        if search:
            domain += ['|', '|',
                        ('name', 'ilike', search),
                        ('author', 'ilike', search),
                        ('isbn', 'ilike', search)]

        # Category filter
        if category:
            domain += [('category', '=', category)]

        # Status filter
        if status_filter == 'rent':
            domain += [('is_rentable', '=', True)]
        elif status_filter == 'sale':
            domain += [('sell_price', '>', 0)]

        # Sort
        order_map = {
            'newest': 'create_date desc',
            'title': 'name asc',
            'price_low': 'sell_price asc',
            'price_high': 'sell_price desc',
        }
        order = order_map.get(sort, 'create_date desc')

        # Pagination
        page = int(page)
        Book = request.env['rumah_buku.book'].sudo()
        total_books = Book.search_count(domain)
        total_pages = max(1, math.ceil(total_books / self.BOOKS_PER_PAGE))
        page = min(max(1, page), total_pages)
        offset = (page - 1) * self.BOOKS_PER_PAGE

        books = Book.search(domain, order=order, limit=self.BOOKS_PER_PAGE, offset=offset)

        # Category list for sidebar
        categories = [
            ('', 'All Books'),
            ('fiction', 'Fiction'),
            ('non_fiction', 'Non-Fiction'),
            ('tech_business', 'Tech & Business'),
            ('science', 'Science'),
            ('history', 'History'),
            ('art_design', 'Art & Design'),
            ('self_help', 'Self Help'),
        ]

        return request.render('rumah_buku.frontend_catalog_page', {
            'books': books,
            'search': search,
            'category': category,
            'status_filter': status_filter,
            'sort': sort,
            'page': page,
            'total_pages': total_pages,
            'total_books': total_books,
            'per_page': self.BOOKS_PER_PAGE,
            'categories': categories,
        })

    @http.route('/book/<int:book_id>', type='http', auth='public', website=True)
    def book_detail(self, book_id, **kwargs):
        book = request.env['rumah_buku.book'].sudo().browse(book_id)
        if not book.exists():
            return request.not_found()

        # Similar books: same category, exclude current
        similar_books = request.env['rumah_buku.book'].sudo().search([
            ('category', '=', book.category),
            ('id', '!=', book.id),
        ], limit=5)

        return request.render('rumah_buku.frontend_book_detail', {
            'book': book,
            'similar_books': similar_books,
        })

    @http.route('/cart/add', type='http', auth='user', website=True, methods=['POST'])
    def cart_add(self, book_id, action_type, duration=10, **kwargs):
        book = request.env['rumah_buku.book'].sudo().browse(int(book_id))
        if book.exists() and book.status == 'available' and book.stock > 0:
            request.env['rumah_buku.transaction'].sudo().create({
                'book_id': book.id,
                'user_id': request.env.user.id,
                'status': 'pending',
                'transaction_type': action_type,
                'borrow_duration_days': int(duration) if action_type == 'borrow' else 0,
            })
        return request.redirect(request.httprequest.referrer or '/catalog')

    @http.route('/cart/remove', type='http', auth='user', website=True, methods=['POST'])
    def cart_remove(self, transaction_id, **kwargs):
        tx = request.env['rumah_buku.transaction'].sudo().browse(int(transaction_id))
        if tx.exists() and tx.user_id.id == request.env.user.id and tx.status == 'pending':
            tx.unlink()
        return request.redirect(request.httprequest.referrer or '/catalog')

    @http.route('/cart/checkout', type='http', auth='user', website=True)
    def checkout_page(self, **kwargs):
        user = request.env.user
        cart_items = request.env['rumah_buku.transaction'].sudo().search([
            ('user_id', '=', user.id),
            ('status', '=', 'pending'),
        ])
        if not cart_items:
            return request.redirect('/catalog')

        total = sum(cart_items.mapped('total_amount'))
        platform_fee = 2000  # Rp 2.000

        return request.render('rumah_buku.frontend_checkout', {
            'cart_items': cart_items,
            'total': total,
            'platform_fee': platform_fee,
            'grand_total': total + platform_fee,
            'checkout_success': False,
        })

    @http.route('/cart/confirm', type='http', auth='user', website=True, methods=['POST'])
    def checkout_confirm(self, **kwargs):
        user = request.env.user
        cart_items = request.env['rumah_buku.transaction'].sudo().search([
            ('user_id', '=', user.id),
            ('status', '=', 'pending'),
        ])

        import uuid
        checkout_token = str(uuid.uuid4())

        for item in cart_items:
            item.sudo().write({
                'status': 'ready_for_pickup',
                'qr_code_token': checkout_token,
                'pickup_date': kwargs.get('pickup_date'),
                'pickup_time': kwargs.get('pickup_time'),
                'notes': f"Payment: {kwargs.get('payment_method', 'qris')}",
            })

        total = sum(cart_items.mapped('total_amount'))
        platform_fee = 2000

        return request.render('rumah_buku.frontend_checkout', {
            'cart_items': cart_items,
            'total': total,
            'platform_fee': platform_fee,
            'grand_total': total + platform_fee,
            'checkout_success': True,
            'checkout_token': checkout_token,
        })

    @http.route('/my-rentals', type='http', auth='user', website=True)
    def my_rentals(self, **kwargs):
        user = request.env.user
        transactions = request.env['rumah_buku.transaction'].sudo().search([
            ('user_id', '=', user.id),
            ('status', '!=', 'pending'),
        ])
        active_rentals = transactions.filtered(
            lambda t: t.status in ['ready_for_pickup', 'borrowed']
        )
        history_rentals = transactions.filtered(
            lambda t: t.status in ['completed', 'cancelled']
        )

        return request.render('rumah_buku.frontend_my_rentals', {
            'active_rentals': active_rentals,
            'history_rentals': history_rentals,
        })

    @http.route('/my-rentals/return', type='http', auth='user', website=True, methods=['POST'])
    def request_return(self, transaction_id, **kwargs):
        """User requests return of a borrowed book."""
        tx = request.env['rumah_buku.transaction'].sudo().browse(int(transaction_id))
        if tx.exists() and tx.user_id.id == request.env.user.id and tx.status == 'borrowed':
            request.env['rumah_buku.transaction_service'].sudo().complete_return(tx.id)
        return request.redirect('/my-rentals')
