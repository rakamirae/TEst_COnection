# -*- coding: utf-8 -*-
{
    'name': 'Employee Mirae',
    'version': '1.0.0',
    'summary': 'Employee For Mirae',
    'sequence': -10,
    'description': """Employee For Mirae Asia Pasifik""",
    'category': 'hr',
    'author': 'Mirae',
    'maintainer': 'Mirae',
    'website': '',
    'license': 'AGPL-3',
    'depends': [ 'base', 'hr',],
    'data': [
        # 'security/ir.model.access.csv', 
        'views/mirae_employee_views.xml',
    ],    
    'installable': True,
    'application': False,
    'auto_install': False,
}