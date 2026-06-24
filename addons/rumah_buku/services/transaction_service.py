from odoo import models, fields, api, _
from odoo.exceptions import UserError
import uuid
from datetime import timedelta


class TransactionService(models.AbstractModel):
    _name = 'rumah_buku.transaction_service'
    _description = 'Layanan Bisnis Transaksi'

    @api.model
    def create_borrow_transaction(self, user_id, book_id, duration_days=10, notes=None):
        """Create a borrow transaction. Default 10 days, after which fines apply."""
        book = self.env['rumah_buku.book'].browse(book_id)
        if not book.exists() or book.status != 'available':
            raise UserError(_("Buku tidak tersedia untuk dipinjam."))
        if book.stock <= 0:
            raise UserError(_("Stok buku habis."))

        transaction = self.env['rumah_buku.transaction'].create({
            'user_id': user_id,
            'book_id': book_id,
            'transaction_type': 'borrow',
            'status': 'pending',
            'borrow_duration_days': duration_days,
            'qr_code_token': str(uuid.uuid4()),
            'notes': notes,
        })

        return transaction

    @api.model
    def confirm_pickup(self, qr_token):
        """Admin scans QR code — confirms book pickup, sets start/due dates."""
        transaction = self.env['rumah_buku.transaction'].sudo().search([
            ('qr_code_token', '=', qr_token),
            ('status', 'in', ['ready_for_pickup']),
        ], limit=1)

        if not transaction:
            raise UserError(_("Token QR tidak valid atau transaksi tidak dalam status siap diambil."))

        now = fields.Datetime.now()
        duration = transaction.borrow_duration_days or 10
        due = now + timedelta(days=duration)

        transaction.write({
            'status': 'borrowed',
            'start_date': now,
            'due_date': due,
        })

        # Update book stock
        book = transaction.book_id
        book.stock = max(book.stock - 1, 0)
        if book.stock == 0:
            book.status = 'borrowed'

        # Create notification for user
        self.env['rumah_buku.notification'].create({
            'user_id': transaction.user_id.id,
            'title': 'Buku Berhasil Diambil',
            'message': f'Buku "{book.name}" berhasil diambil. Harap dikembalikan sebelum {due.strftime("%d %b %Y")}.',
            'notification_type': 'order_update',
        })

        return transaction

    @api.model
    def complete_return(self, transaction_id):
        """Process book return. Auto-creates fine if overdue (>10 days)."""
        transaction = self.env['rumah_buku.transaction'].browse(transaction_id)
        if not transaction.exists() or transaction.status != 'borrowed':
            raise UserError(_("Transaksi tidak valid untuk pengembalian."))

        now = fields.Datetime.now()
        transaction.write({
            'status': 'completed',
            'returned_date': now,
        })

        # Restore book stock
        book = transaction.book_id
        book.stock += 1
        if book.status == 'borrowed':
            book.status = 'available'

        # Check for overdue — if past due_date, create fine
        if transaction.due_date and now > transaction.due_date:
            overdue_days = (now - transaction.due_date).days
            fine_per_day = 5000  # Rp 5.000 per hari keterlambatan
            fine_amount = overdue_days * fine_per_day

            self.env['rumah_buku.fine'].create({
                'transaction_id': transaction.id,
                'user_id': transaction.user_id.id,
                'amount': fine_amount,
                'reason': 'late_return',
            })

            # Notify user about fine
            self.env['rumah_buku.notification'].create({
                'user_id': transaction.user_id.id,
                'title': 'Denda Keterlambatan',
                'message': f'Anda dikenakan denda Rp {fine_amount:,.0f} karena terlambat {overdue_days} hari mengembalikan "{book.name}".',
                'notification_type': 'fine_alert',
            })
        else:
            # Notify successful return
            self.env['rumah_buku.notification'].create({
                'user_id': transaction.user_id.id,
                'title': 'Buku Berhasil Dikembalikan',
                'message': f'Buku "{book.name}" berhasil dikembalikan. Terima kasih!',
                'notification_type': 'order_update',
            })

        return transaction
