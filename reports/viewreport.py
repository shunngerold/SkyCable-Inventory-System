from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
class drops_issuance_xml_class(models.AbstractModel):
   _name = 'report.skycable_employee_inventory.drop_issuance_report'

   @api.model
   def render_html(self, docids, data=None):
      # docs = self.env['stock.drops.issuance'].browse(docids)
      item1 = self.env['stock.drops.issuance'].search([('id', '=', docids)])
      table1 = []
      for rec in item1:
         vals = {
         'callid': rec.callid,
         'import_batch': rec.import_batch,
         'employee_name': rec.employee_name.name,
         'date_time': rec.date_time,
         'stats': rec.stats,
         # 'etsi_product_name': rec.etsi_product_name,
         'task_type_category': rec.task_type_category,
         'assigned_engineer': rec.assigned_engineer,
         'completion_date': rec.completion_date,
         'ref_number': rec.ref_number,
         'counter_drops': rec.counter_drops,
        #  'etsi_date_returned_in': rec.etsi_date_returned_in,
        #  'etsi_team_in': rec.etsi_team_in,
        #  'etsi_status': rec.etsi_status,
        #  'etsi_description': rec.etsi_description,

         }
         table1.append(vals)
      docargs = {
         'table1': table1,
         }
      
      return self.env['report'].render('skycable_employee_inventory.drop_issuance_report', docargs)


   