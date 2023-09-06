from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_utils

class ProductDetails(models.Model):
    _inherit = 'stock.inventory'
    
    # fields
    etsi_product_detail =  fields.One2many('etsi.product.detail.line','etsi_product_ids')
    etsi_product_detail_2 =  fields.One2many('etsi.product.detail.line.two','etsi_product_ids_2')
    lineidscount2 =  fields.Integer(compute='get_count_lineids2')
    filter = fields.Selection(selection='_selection_filter_test')
    filter2 = fields.Selection(related='product_id.internal_ref_name')
    employee_name_inv = fields.Many2one('res.users',String="Employee Name", default=lambda self: self.env.user.id, required=True)
    receive_date_inv = fields.Date(string="Received Date", required=True,default=fields.Date.today())
    name = fields.Char(required=True, copy=False, readonly=True, default = lambda self : ('New'))

    @api.multi
    @api.onchange('line_ids')
    def remove_connected(self):
        checker1 =[]
        result =[]
        result2 =[]
        for rec in self:
            for checkdata in self.line_ids:
                checker1.append(checkdata.product_id.id)

            for record in self.line_ids:
                for line in self.etsi_product_detail:
                    if line.etsi_products.id not in checker1:
                        pass
                    else:
                        result.append(( 0, 0,{
                            'etsi_serials':line.etsi_serials,
                            'etsi_macs': line.etsi_macs,
                            'etsi_products': line.etsi_products.id,
                            'sky_receive_date':line.sky_receive_date,
                            'sky_subscriber': line.sky_subscriber,
                            'sky_date_issued': line.sky_date_issued,
                            'sky_date_returned': line.sky_date_returned,
                            'sky_team': line.sky_team,
                            'sky_time_punch': line.sky_time_punch,
                        }))

            for record in self.line_ids:
                for line in self.etsi_product_detail_2:
                    if line.etsi_products_2.id not in checker1:
                        pass
                    else:
                        result2.append(( 
                            0, 0,{
                                'etsi_serials_2':line.etsi_serials_2,
                                'etsi_smart_card_2': line.etsi_smart_card_2,
                                'etsi_products_2': line.etsi_products_2.id,
                                'sky_receive_date_2': line.sky_receive_date_2,
                                'sky_subscriber': line.sky_subscriber_2,
                                'sky_date_issued': line.sky_date_issued_2,
                                'sky_date_returned': line.sky_date_returned_2,
                                'sky_team': line.sky_team_2,
                                'sky_time_punch_2': line.sky_time_punch_2,
                        }))

            a = [ item for pos,item in enumerate(result) if result.index(item)==pos ]
            b = [ item for pos,item in enumerate(result2) if result2.index(item)==pos ]

            self.etsi_product_detail = a
            self.etsi_product_detail_2 = b
    
    @api.depends('line_ids')
    def get_count_lineids2(self):
        for rec in self:
            count = len(self.line_ids)
            rec.lineidscount2 = count

    @api.multi
    @api.onchange('etsi_product_detail','etsi_product_detail_2')
    def add_quantity_method(self): 
        for rec in self:
            test2 = []
            test = []

            for line in self.line_ids:
                if line not in test2:
                    test2.append(line.product_id.id)

            for line2 in self.etsi_product_detail:
                test.append((
                    0, 0, {
                        'product_id': line2.etsi_products.id,
                        'location_id': self.location_id.id,
                        'company_id': self.company_id.id,
                        'product_uom_id': line2.etsi_products.product_tmpl_id.uom_id.id,
                    }
                ))

            for line2 in self.etsi_product_detail_2:
                test.append((
                    0, 0, {
                        'product_id': line2.etsi_products_2.id,
                        'location_id': self.location_id.id,
                        'company_id': self.company_id.id,
                        'product_uom_id': line2.etsi_products_2.product_tmpl_id.uom_id.id,
                    }
                ))
            
            removing_duplicate = [ item for pos,item in enumerate(test) if test.index(item)==pos ]
            self.line_ids = removing_duplicate

            for line in self.line_ids:
                count = line.theoretical_qty
                for line2 in self.etsi_product_detail:
                    if line.product_id.id == line2.etsi_products.id:
                        count += 1
                line.product_qty = count
                for line3 in self.etsi_product_detail_2:
                    if line.product_id.id == line3.etsi_products_2.id:
                        count += 1
                line.product_qty = count

    # CREATE VALIDATION  
    @api.model
    def create(self, vals):
        vals['name']  = self.env['ir.sequence'].next_by_code('skycable.inventory.adjustment.sequence') or _('New')
        res = super(ProductDetails, self).create(vals)
        return res

    # overide actiondone
    @api.multi
    def action_done(self):
        res = super(ProductDetails, self).action_done()
        if len(self.line_ids) == 0:
            raise ValidationError(('Inventory details table can not be empty.'))

        if self.filter2 == 'broadband':
            for line in self.etsi_product_detail:
                self.env['etsi.inventory'].create({
                    'etsi_serial': line.etsi_serials,
                    'etsi_mac':line.etsi_macs,
                    'type_checker_02':line.etsi_products.internal_ref_name,
                    'etsi_product_id':line.etsi_products.id,
                    'etsi_product_name':line.etsi_products.id,
                    'etsi_product_quantity': 1,
                    'etsi_receive_date_in':line.sky_receive_date,
                    'etsi_subscriber_in': line.sky_subscriber,
                    'etsi_date_issued_in': line.sky_date_issued,
                    'etsi_date_returned_in': line.sky_date_returned,
                    'etsi_team_in': line.sky_team,
                    'etsi_punched_date_in': line.sky_time_punch,
                    'etsi_employee_in': self.employee_name_inv.id,
                })
        elif self.filter2 == 'catv5':
            for line in self.etsi_product_detail_2:
                self.env['etsi.inventory'].create({
                    'etsi_serial': line.etsi_serials_2,
                    'etsi_smart_card':line.etsi_smart_card_2,
                    'type_checker_02':line.etsi_products_2.internal_ref_name,
                    'etsi_product_id':line.etsi_products_2.id,
                    'etsi_product_name':line.etsi_products_2.id,
                    'etsi_product_quantity': 1,
                    'etsi_receive_date_in':line.sky_receive_date_2,
                    'etsi_subscriber_in': line.sky_subscriber_2,
                    'etsi_date_issued_in': line.sky_date_issued_2,
                    'etsi_date_returned_in': line.sky_date_returned_2,
                    'etsi_team_in': line.sky_team_2,
                    'etsi_punched_date_in': line.sky_time_punch_2,
                    'etsi_employee_in': self.employee_name_inv.id,
                })

        elif self.filter2=='drops' or self.filter2 == 'others':
            pass
        else:
            for line in self.etsi_product_detail:
                self.env['etsi.inventory'].create({
                    'etsi_serial': line.etsi_serials,
                    'etsi_mac':line.etsi_macs,
                    'etsi_product_id':line.etsi_products.id,
                    'etsi_product_name':line.etsi_products.id,
                    'etsi_receive_date_in':line.sky_receive_date,
                    'etsi_subscriber_in': line.sky_subscriber,
                    'etsi_date_issued_in': line.sky_date_issued,
                    'etsi_date_returned_in': line.sky_date_returned,
                    'etsi_team_in': line.sky_team,
                    'etsi_punched_date_in': line.sky_time_punch,
                    'etsi_employee_in': self.employee_name_inv.id,
                    })
            for line in self.etsi_product_detail_2:
                self.env['etsi.inventory'].create({
                    'etsi_serial': line.etsi_serials_2,
                    'etsi_smart_card':line.etsi_smart_card_2,
                    'etsi_product_id':line.etsi_products_2.id,
                    'etsi_product_name':line.etsi_products_2.id,
                    'etsi_receive_date_in':line.sky_receive_date_2,
                    'etsi_subscriber_in': line.sky_subscriber_2,
                    'etsi_date_issued_in': line.sky_date_issued_2,
                    'etsi_date_returned_in': line.sky_date_returned_2,
                    'etsi_team_in': line.sky_team_2,
                    'etsi_punched_date_in': line.sky_time_punch_2,
                    'etsi_employee_in': self.employee_name_inv.id,

                    })
        return res

    # ******    HIDE RADIO BUTTONS (WIDGET): ALL PRODUCTS AND ONE PRODUCT CATEGORY
    @api.model
    def _selection_filter_test(self):
        """ Get the list of filter allowed according to the options checked
        in 'Settings\Warehouse'. """
        res_filter = [
            ('product', _('One product only')),
            ('partial', _('Select products manually'))]

        if self.user_has_groups('stock.group_tracking_owner'):
            res_filter += [('owner', _('One owner only')), ('product_owner', _('One product for a specific owner'))]
        if self.user_has_groups('stock.group_production_lot'):
            res_filter.append(('lot', _('One Lot/Serial Number')))
        if self.user_has_groups('stock.group_tracking_lot'):
            res_filter.append(('pack', _('A Pack')))
        return res_filter

class ProductAdjustment(models.Model):
    _name = 'etsi.product.detail.line'
    
    etsi_product_ids = fields.Many2one('stock.inventory')
    etsi_serials = fields.Char(string="Serial ID", )
    etsi_macs = fields.Char(string="MAC ID")
    etsi_products = fields.Many2one('product.product', string="Products", required=True)
    type_checker = fields.Selection(related='etsi_products.internal_ref_name')

    # ADDING NEW FIELDS
    sky_receive_date = fields.Date("Receive Date", related='etsi_product_ids.receive_date_inv')
    sky_subscriber = fields.Char("Subscriber")
    sky_date_issued = fields.Date("Date Issued")
    sky_date_returned = fields.Date("Returned Date")
    sky_team = fields.Char("Team")
    sky_time_punch = fields.Datetime(string="Punch Time",default=fields.Datetime.now, readonly="True")

    @api.model
    def _selection_filter(self):
        res_filter = [
            ('none', _('All products')),
            ('category', _('One product category')),
            ('product', _('One product only')),
            ('partial', _('Select products manually'))]
        return res_filter
    
    etsi_filter = fields.Selection(
        string='Inventory of', selection='_selection_filter',
        default='none',
        help="If you do an entire inventory, you can choose 'All Products' and it will prefill the inventory with the current stock.  If you only do some products  "
             "(e.g. Cycle Counting) you can choose 'Manual Selection of Products' and the system won't propose anything.  You can also let the "
             "system propose for a single product / lot /... ")

class ProductAdjustment_02(models.Model):
    _name = 'etsi.product.detail.line.two'

    etsi_product_ids_2 = fields.Many2one('stock.inventory')
    etsi_serials_2 = fields.Char(string="Serial ID")
    etsi_smart_card_2 = fields.Char(string="Smart Card")
    etsi_products_2 = fields.Many2one('product.product', string="Products", required=True)
    type_checker_2 = fields.Selection(related='etsi_products_2.internal_ref_name')
    sky_receive_date_2 = fields.Date("Receive Date", related='etsi_product_ids_2.receive_date_inv')
    sky_subscriber_2 = fields.Char("Subscriber")
    sky_date_issued_2 = fields.Date("Date Issued")
    sky_date_returned_2 = fields.Date("Returned Date")
    sky_team_2 = fields.Char("Team")
    sky_time_punch_2 = fields.Datetime(string="Punch Time",default=fields.Datetime.now, readonly="True")

    @api.model
    def _selection_filter(self):
        res_filter = [
            ('none', _('All products')),
            ('category', _('One product category')),
            ('product', _('One product only')),
            ('partial', _('Select products manually'))]
        return res_filter
    
    etsi_filter_2 = fields.Selection(
        string='Inventory of', selection='_selection_filter',
        default='none',
        help="If you do an entire inventory, you can choose 'All Products' and it will prefill the inventory with the current stock.  If you only do some products  "
             "(e.g. Cycle Counting) you can choose 'Manual Selection of Products' and the system won't propose anything.  You can also let the "
             "system propose for a single product / lot /... ")