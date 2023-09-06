from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
class view_all_serial_report(models.AbstractModel):
   _name = 'report.skycable_employee_inventory.all_serial_report'

   @api.model
   def render_html(self, docids, data=None):
      # docs = self.env['etsi.inventory'].browse(docids)
      item1 = self.env['etsi.inventory'].search([('id', '=', docids)])
      table1 = []
      for rec in item1:
         vals = {
         'etsi_serial': rec.etsi_serial,
         'etsi_mac': rec.etsi_mac,
         'etsi_smart_card': rec.etsi_smart_card,
         'etsi_employee_in': rec.etsi_employee_in.name,
         'etsi_product_id': rec.etsi_product_id.name,
         # 'etsi_product_name': rec.etsi_product_name,
         'type_checker': rec.type_checker.upper(),
         'etsi_punched_date_in': rec.etsi_punched_date_in,
         'etsi_subscriber_in': rec.etsi_subscriber_in,
         'etsi_receive_date_in': rec.etsi_receive_date_in,
         'etsi_date_issued_in': rec.etsi_date_issued_in,
         'etsi_date_returned_in': rec.etsi_date_returned_in,
         'etsi_team_in': rec.etsi_team_in,
         'etsi_status': rec.etsi_status,
         'etsi_description': rec.etsi_description,

         }
         table1.append(vals)
      docargs = {
         'table1': table1,
         }
      
      return self.env['report'].render('skycable_employee_inventory.all_serial_report', docargs)


   