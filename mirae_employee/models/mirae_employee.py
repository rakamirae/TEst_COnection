from odoo import api, fields, models, _

class MiraeEmployee(models.Model):
    _inherit = 'hr.employee'
    
    employee_number = fields.Char(name="Employee Number", required=True)
    staff = fields.Boolean(string="Staff", default=True)

    _sql_constraints = [
        ('uniq_employee_number', 'unique(employee_number)', 
         "A Employee Number already exists with this name . Employee Number must be unique!"),
    ]