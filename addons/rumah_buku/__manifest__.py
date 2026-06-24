{
    'name': 'Rumah Buku',
    'version': '2.0',
    'summary': 'Manajemen Toko Buku & Peminjaman (Gelari Medika)',
    'description': """
        Modul Odoo 19 untuk mengelola Toko Buku Rumah Buku.
        Mencakup:
        - Katalog Buku dengan search, filter, pagination
        - Peminjaman & Pembelian dengan QR Code
        - Pembayaran (Mock) & Denda otomatis
        - Keanggotaan Bulanan
        - Notifikasi real-time
        - Admin Portal: Dashboard, Inventory, Users, Transactions, Financial, QR Scanner
        - API Backend & UI Frontend terintegrasi
    """,
    'author': 'Antigravity',
    'category': 'Sales/Rumah Buku',
    'depends': ['base', 'web', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/frontend_templates.xml',
        'views/frontend_auth.xml',
        'views/frontend_portal.xml',
        'views/admin_portal.xml',
        'data/seed_books.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'rumah_buku/static/src/css/style.css',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
