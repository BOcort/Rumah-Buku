from odoo import http
from odoo.http import request
import json
import math


class BookController(http.Controller):

    @http.route('/api/books', type='http', auth='public', methods=['GET'], csrf=False)
    def get_books(self, search='', category='', status='', page=1, limit=12, **kwargs):
        """API: Get list of books with search, filter, and pagination."""
        domain = []
        if search:
            domain += ['|', '|',
                        ('name', 'ilike', search),
                        ('author', 'ilike', search),
                        ('isbn', 'ilike', search)]
        if category:
            domain += [('category', '=', category)]
        if status:
            domain += [('status', '=', status)]

        Book = request.env['rumah_buku.book'].sudo()
        page = int(page)
        limit = int(limit)
        total = Book.search_count(domain)
        total_pages = max(1, math.ceil(total / limit))
        offset = (page - 1) * limit

        books = Book.search(domain, limit=limit, offset=offset, order='create_date desc')
        data = []
        for b in books:
            data.append({
                'id': b.id,
                'name': b.name,
                'author': b.author,
                'isbn': b.isbn,
                'category': b.category,
                'status': b.status,
                'stock': b.stock,
                'sell_price': b.sell_price,
                'rent_price_per_day': b.rent_price_per_day,
                'is_rentable': b.is_rentable,
                'cover_url': b.cover_display_url,
                'publication_year': b.publication_year,
                'pages': b.pages,
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

    @http.route('/api/books/<int:book_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_book_detail(self, book_id, **kwargs):
        """API: Get single book detail."""
        book = request.env['rumah_buku.book'].sudo().browse(book_id)
        if not book.exists():
            return request.make_response(
                json.dumps({'error': 'Not Found'}),
                status=404,
                headers=[('Content-Type', 'application/json')]
            )

        data = {
            'id': book.id,
            'name': book.name,
            'author': book.author,
            'isbn': book.isbn,
            'publisher': book.publisher,
            'synopsis': book.synopsis,
            'category': book.category,
            'status': book.status,
            'stock': book.stock,
            'sell_price': book.sell_price,
            'rent_price_per_day': book.rent_price_per_day,
            'is_rentable': book.is_rentable,
            'cover_url': book.cover_display_url,
            'publication_year': book.publication_year,
            'pages': book.pages,
            'location_rack': book.location_rack,
        }
        return request.make_response(
            json.dumps({'status': 'success', 'data': data}),
            headers=[('Content-Type', 'application/json')]
        )

    @http.route('/api/books', type='http', auth='user', methods=['POST'], csrf=False)
    def create_book(self, **kwargs):
        """API: Create a new book (admin only)."""
        if not request.env.user.has_group('base.group_system'):
            return request.make_response(
                json.dumps({'error': 'Forbidden'}),
                status=403,
                headers=[('Content-Type', 'application/json')]
            )

        try:
            data = json.loads(request.httprequest.data)
            book = request.env['rumah_buku.book'].sudo().create({
                'name': data.get('name'),
                'author': data.get('author'),
                'isbn': data.get('isbn', ''),
                'publisher': data.get('publisher', ''),
                'synopsis': data.get('synopsis', ''),
                'category': data.get('category', 'other'),
                'sell_price': data.get('sell_price', 0),
                'rent_price_per_day': data.get('rent_price_per_day', 5000),
                'stock': data.get('stock', 1),
                'location_rack': data.get('location_rack', ''),
                'publication_year': data.get('publication_year', ''),
                'pages': data.get('pages', 0),
                'cover_url': data.get('cover_url', ''),
            })
            return request.make_response(
                json.dumps({'status': 'success', 'id': book.id, 'message': 'Book created successfully'}),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            return request.make_response(
                json.dumps({'error': str(e)}),
                status=400,
                headers=[('Content-Type', 'application/json')]
            )
