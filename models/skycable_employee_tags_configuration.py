# -*- coding: utf-8 -*-\\
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Employee_Default_Category(models.Model):
    _inherit ='hr.employee.category'

    default_emp_category = fields.Boolean(string="Default Category" )
       
class Employees(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def default_get(self, fields):
        result = super(Employees, self).default_get(fields)
        result['category_ids'] =  self.env['hr.employee.category'].search([ ('default_emp_category', '=', True)]).ids
        result['emp_categ_id'] = self.env['hr.employee.category'].search([ ('default_emp_category', '=', True)]).id
     
        return result

    @api.model 
    def create(self,vals):
        # Dictionary to hold the selected ids
        list_category = {} 
        # Dictionary to hold the default employee id
        list_category_emp_id = {}

        list_category =str(vals.get('category_ids')) 
        list_category_emp_id = str(vals.get('emp_categ_id'))
      
        if not vals.get('first_name','last_name'):
            raise ValidationError("Please complete employee name")

        elif not vals.get('category_ids','emp_categ_id'):
            raise ValidationError("Please select employee category tags")

        elif list_category_emp_id not in list_category:
            raise ValidationError("Please make sure that selected employee tags and employee category matched")
 
        res = super(Employees, self).create(vals)
        return res 

    @api.multi
    def write(self, vals):
        # Either 1 field are changed in vals, activate this code
        if 'emp_categ_id' or 'category_ids' in vals:

            # Dictionary to hold the selected ids
            list_category = {} 
            # Dictionary to hold the default employee id
            list_category_emp_id = {}
             
            list_category = str(vals.get('category_ids'))
            list_category_emp_id = str(vals.get('emp_categ_id'))
            
            if list_category_emp_id not in list_category:
                raise ValidationError("Please make sure that selected employee tags and employee category matched")

            elif not vals.get('category_ids','emp_categ_id'):
                raise ValidationError("Please select employee category tags")

        # When both fields are changed in vals, activate this code
        if 'category_ids' and 'emp_categ_id' in vals:
            # Dictionary to hold the selected ids
            list_category = {} 
            # Dictionary to hold the default employee id
            list_category_emp_id = {}
            list_category = str(vals.get('category_ids'))
            list_category_emp_id = str(vals.get('emp_categ_id'))
            
            if list_category_emp_id not in list_category:
                raise ValidationError("Please make sure that selected employee tags and employee category matched")

            elif not vals.get('category_ids','emp_categ_id'):
                raise ValidationError("Please select employee category tags")
 
        res = super(Employees, self).write(vals)
        return res
 
class Employee_Default_Categories(models.Model):
    _inherit ='hr.employee.category'
 
    @api.constrains('default_emp_category')
    def _check_date_end(self):
        for record in self:
            counter = self.env['hr.employee.category'].search_count([ ('default_emp_category', '=', True)])
            if counter > 1:
                raise ValidationError("Can not set more than one default employee category")
