from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
class view_all_pull_out_report(models.AbstractModel):
   _name = 'report.skycable_employee_inventory.view_all_pull_out_report'

   @api.model
   def render_html(self, docids, data=None):
      # docs = self.env['etsi.inventory'].browse(docids)
      item1 = self.env['etsi.pull_out.inventory'].search([('id', '=', docids)])
      table1 = []
      for rec in item1:
         vals = {
         'job_number': rec.job_number,
         'serial_type': rec.serial_type.upper(),
         'etsi_serial': rec.etsi_serial,
         'etsi_mac': rec.etsi_mac,
         'etsi_smart_card': rec.etsi_smart_card,
         'etsi_receive_date_in': rec.etsi_receive_date_in,
         'etsi_date_issued_in': rec.etsi_date_issued_in,
         'etsi_date_returned_in': rec.etsi_date_returned_in,
         'employee_number': rec.employee_number.name,
         'etsi_status': rec.etsi_status,
         'transaction_number': rec.transaction_number,
         'description' : rec.description
         }
         table1.append(vals)
      docargs = {
         'table1': table1,
         }
      
      return self.env['report'].render('skycable_employee_inventory.view_all_pull_out_report', docargs)


   