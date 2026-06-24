# Odoo Shell Script to reset admin password
user = env['res.users'].search([('login', '=', 'admin@email.com')], limit=1)

if not user:
    # Create it if it doesn't exist, linked to Administrator
    admin_user = env.ref('base.user_admin')
    admin_user.write({
        'login': 'admin@email.com',
        'password': 'admin#123',
        'name': 'Administrator'
    })
    print("\n✅ Default Admin account updated to admin@email.com")
else:
    # Just update the password and ensure it has admin rights
    user.write({
        'password': 'admin#123',
        'groups_id': [(4, env.ref('base.group_system').id)]
    })
    print("\n✅ Password for admin@email.com reset to admin#123 and admin rights granted")

env.cr.commit()
