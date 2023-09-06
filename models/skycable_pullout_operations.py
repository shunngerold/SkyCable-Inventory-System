from odoo import api, fields, models, _
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from odoo.exceptions import ValidationError, UserError

class Validate_Pullout_Received(models.Model):
    _inherit = 'stock.picking'

    pullout_holder = fields.One2many('pullout_picking_child','pullout_picking_child_connector')
    pullout_holder_return = fields.One2many('pullout_picking_child_return','pullout_picking_child_connector_2')

    # Returned items
    pullout_return_list = fields.One2many('pullout_picking_child_return_list','pullout_return_list_connector')

    # Fields after the delivery 
    employee_for_delivery = fields.Many2one('hr.employee') 
    date_delivered = fields.Date(string="Date Returned")
    received_by = fields.Char(string="Received By: ")

    # Count all etsi.inventory.pullouts
    etsi_pullout_count = fields.Integer(string="Pull-Out Counts")
    etsi_pullout_count_temp = fields.Integer(string="Quantity")
    etsi_pullout_count_temp_related = fields.Integer(string="Quantity", related="etsi_pullout_count_temp", readonly="True")
    pullout_return_quantity = fields.Integer(string="Quantity")
    pullout_return_quantity_related = fields.Integer(string="Quantity",related="pullout_return_quantity", readonly="True")
    pullout_returned_quantity = fields.Integer(string="Returned Quantity")
    # Detects what type of serial
    serial_type = fields.Selection([('catv', 'CATV'),('modem', 'Modem')], default='catv')

    # Detects what type of serial
    status_field = fields.Selection([('draft', 'Draft'),('waiting', 'Waiting For Delivery Team'),('done', 'Done')], default='draft')
    
    # Detects how many lines to process
    line_counter = fields.Integer('First: ')
    
    @api.multi
    def action_cancel(self):
        if self.teller == 'subscriber':
            self.update({'state' :'cancel'})

        if self.teller == 'pull-out':
            self.update({'state' :'cancel'})

        if self.teller == 'pull-out-return':
            product_lists = []
            product_serials = []

            # Update the date of delivery to sky cable of pull outs
            for rec in self:
                for plines_issued in rec.pullout_holder_return:
                    if plines_issued.for_delivery == True:
                        product_lists.append(plines_issued.etsi_serial_product)
                        product_serials.append(plines_issued.etsi_serial_product)
                        issued_stats = self.env['pullout_picking_child_return'].search([])
                        inventory_stats = self.env['etsi.pull_out.inventory'].search([])

                        # To update the status of serials as returned from sky 
                        if product_serials:
                            for searched_ids in inventory_stats:
                                if searched_ids.etsi_serial in product_serials:
                                    searched_ids.update({'etsi_status': 'received',
                                    })
                
                if self.status_field == 'waiting':
                    for plines_issued in rec.pullout_return_list:
                        if plines_issued.for_delivery == True:

                            product_lists.append(plines_issued.etsi_serial_product)
                            product_serials.append(plines_issued.etsi_serial_product)
                            issued_stats = self.env['pullout_picking_child_return'].search([])
                            inventory_stats = self.env['etsi.pull_out.inventory'].search([])

                            # To update the status of serials as returned from sky 
                            if product_serials:
                                for searched_ids in inventory_stats:
                                    if searched_ids.etsi_serial in product_serials:
                                        searched_ids.update({
                                            'etsi_status': 'received',
                                            'etsi_date_issued_in' : False,
                                            'status_field' : 'draft'
                                        })
                                        
            self.update({'state' :'cancel'})
    
    # Detects how many lines per batch, will be transferred 
    @api.onchange('line_counter')
    def set_num_lines(self):
        return_lines = []
        return_res =self.env['etsi.pull_out.inventory'].search([('etsi_status', 'in', ('received', 'damaged')),('status_field', 'not in', ('waiting', 'done'))])
        counter = 0 
        date = fields.date.today()

        for item in return_res:
            if item.etsi_status == 'received' or item.is_damaged == True :
                return_lines.append(( 0,0, {
                    'for_delivery': True,  
                    'job_number' : item.job_number,     
                    'job_number_related' : item.job_number,
                    'product_id' : item.etsi_product_name,
                    'product_id_related' : item.etsi_product_name,
                    'etsi_mac_product': item.etsi_mac,
                    'etsi_serial_product' : item.etsi_serial,
                    'etsi_mac_product' : item.etsi_mac,
                    'etsi_smart_card' : item.etsi_smart_card,
                    'comp_date' : date,
                    'etsi_teams_id' : item.etsi_teams_id,
                    'issued' : item.etsi_status,
                    'employee_number' : item.employee_number,
                    'is_damaged': item.is_damaged,
                    'description' : item.description
                }))

            counter += 1
            if counter == self.line_counter :
                break
        self.update({'pullout_holder_return' : return_lines })

    # Register the serial to the etsi.inventory 
    # Date can not be set from the past 
    @api.constrains('date_delivered')
    def check_date(self):
        if self.date_delivered == False:
            pass
        if self.date_delivered < fields.Date.today():
            raise ValidationError("The date cannot be set in the past")
    
    def _count_pullouts(self):
        for rec in self:
            rec.etsi_pullout_count = self.env['etsi.pull_out.inventory'].search_count([('etsi_status','in', ('received','delivery'))])
    
    @api.onchange('pullout_holder')
    def check_pullut_count(self):
        count = self.env['etsi.pull_out.inventory'].search_count([('etsi_status','in', ('received','delivery'))])
        count2 = 0 
        
        for rec in self:
            for lines in rec.pullout_holder :
                count += 1
                count2 += 1

        self.update({
            'etsi_pullout_count_temp' :  count2
        })

    # Load count for the checked items
    @api.onchange('pullout_holder_return')
    def check_pullout_counter(self):
        count = 0 
        
        for rec in self:
            for lines in rec.pullout_holder_return :
                if lines.for_delivery == True:
                    count += 1

        self.update({
            'pullout_return_quantity' :  count
        })

    @api.model
    def default_get(self, fields):
        res = super(Validate_Pullout_Received, self).default_get(fields)
        res['etsi_pullout_count'] = self.env['etsi.pull_out.inventory'].search_count([('etsi_status','in', ('received','delivery')),('status_field', 'not in', ('waiting', 'done'))])
        
        return res

    @api.multi
    def do_new_transfer(self):
        res = super(Validate_Pullout_Received, self).do_new_transfer()

        for rec in self:
            teller = rec.teller
        
        if teller == 'pull-out':
            picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
            # Code sa pag create
            stock_picking_db = self.env['etsi.pull_out.inventory']

            listahan = []   
            for rec in self:
                search_name = self.env['stock.picking'].search([('name','=',rec.name)])
                picking_checker = self.env['stock.picking'].search([('picking_type_id.name','=', 'Subscriber Issuance')])
                
                for x in rec.pullout_holder:
                    listahan.append({
                        'job_number': x.job_number,
                        'etsi_product_name' : x.product_id,
                        'etsi_serial' : x.etsi_serial_product,
                        'etsi_mac': x.etsi_mac_product,
                        'etsi_smart_card': x.etsi_smart_card ,
                        'etsi_employee_in' : 'Administrator',
                        'etsi_teams_id' : rec.etsi_teams_id,
                        'etsi_receive_date_in' : x.comp_date,
                    })
                            
            for rec in self:
                employee_id = rec.etsi_teams_id.team_number

            for laman in listahan:
                stock_picking_db = self.env['etsi.pull_out.inventory']
                stock_picking_db.create({
                    'job_number' : laman['job_number'], 
                    'etsi_product_name' : laman['etsi_product_name'],
                    'etsi_serial': laman['etsi_serial'],
                    'etsi_mac': laman['etsi_mac'],
                    'etsi_smart_card': laman['etsi_smart_card'],
                    'etsi_employee_in': laman['etsi_employee_in'],
                    'etsi_teams_id' : employee_id,
                    'etsi_status': 'received',
                    'etsi_receive_date_in': laman['etsi_receive_date_in'],
                })        

            picking_checker2 = self.env['stock.picking.type'].search([('name', '=', 'Pullout Receive')])
            stock_picking_db = self.env['stock.picking']
            
            self.update({
                'picking_type_id': picking_checker2.id,
                'location_id': picking_checker2.default_location_src_id.id,
                'location_dest_id': picking_checker2.default_location_dest_id.id,
                'etsi_teams_id':  picking.etsi_teams_id.id,
                'state' : 'done'
            })

        if teller == 'pull-out-return':
            picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
            # Code sa pag create
            stock_picking_db = self.env['etsi.pull_out.inventory']

            if rec.pullout_holder_return == False:
                raise ValidationError("Please fill up items to return to sky")

            listahan = []
            for rec in self:
                search_name = self.env['stock.picking'].search([('name','=',rec.name)])
                picking_checker = self.env['stock.picking'].search([('picking_type_id.name','=', 'Pullout Return To Sky')])
                
                for x in rec.pullout_holder_return:
                    listahan.append({
                        'job_number': x.job_number,
                        'etsi_product_name' : x.product_id,
                        'etsi_serial' : x.etsi_serial_product,
                        'etsi_mac': x.etsi_mac_product,
                        'etsi_smart_card': x.etsi_smart_card ,
                        'etsi_employee_in' : 'Administrator',
                        'etsi_teams_id' : rec.etsi_teams_id,
                        'etsi_punched_date_in' : x.comp_date,
                        'etsi_date_returned_in' : x.comp_date,
                    })

            picking_checker2 = self.env['stock.picking.type'].search([('name', '=', 'Pullout Return To Sky')])
            stock_picking_db = self.env['stock.picking']
            self.update({'state' : 'waiting'})

        return res

    @api.multi
    def receive_pullout_btn(self):
        picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
        listahan_delivery = []

        for rec in self:
            if rec.pullout_holder:
                search_name = self.env['stock.picking'].search([('name','=',rec.name)])
                picking_checker = self.env['stock.picking'].search([('picking_type_id.name','=', 'Pullout Receive')])
            
                for x in rec.pullout_holder:
                    # For Broadband 
                    if x.serial_type == 'catv' and x.etsi_serial_product == False:
                        raise ValidationError("Please make sure to fill Serial ID")
                    if x.serial_type == 'modem' and x.etsi_mac_product == False:
                        raise ValidationError("Please make sure to fill MAC ID")
                    else:
                        listahan_delivery.append(( 0, 0,{
                            'name': x.product_id,
                            'product_id': 1, 
                            'product_uom_qty' : x.product_uom_qty, 
                            'product_uom' : x.product_uom.id,
                            'move_id': x.id, 
                            'issued_field': "On Hand",
                            'etsi_serials_field': x.etsi_serial_product, 
                            'etsi_mac_field': x.etsi_mac_product, 
                            'etsi_smart_card_field': x.etsi_smart_card,
                            'state' : 'draft',
                            'location_id' : rec.location_id,
                            'location_dest_id' : rec.location_dest_id,
                            'picking_type_id': rec.picking_type_id,
                            'etsi_teams_id' : x.etsi_teams_id
                        }))
                        
                picking_checker2 = self.env['stock.picking.type'].search([('name', '=', 'Pullout Receive')])
                stock_picking_db = self.env['stock.picking']
                
                # CREATE RECORD
                picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
                # Code sa pag create
                stock_picking_db = self.env['etsi.pull_out.inventory']

                listahan = []
                for rec in self:
                    search_name = self.env['stock.picking'].search([('name','=',rec.name)])
                    picking_checker = self.env['stock.picking'].search([('picking_type_id.name','=', 'Pullout Receive')])
                    
                    for x in rec.pullout_holder:
                        listahan.append({
                            'job_number': x.job_number,
                            'etsi_product_name' : x.product_id,
                            'etsi_serial' : x.etsi_serial_product,
                            'etsi_mac': x.etsi_mac_product,
                            'etsi_smart_card': x.etsi_smart_card ,
                            'etsi_employee_in' : 'Administrator',
                            'etsi_teams_id' : rec.etsi_teams_id,
                            'employee_number': x.employee_number.id,
                            'etsi_receive_date_in' : x.comp_date,
                            'name' : rec.name,
                            'serial_type' : x.serial_type,
                            'description' : x.description
                        })
                                
                for rec in self:
                    employee_id = rec.etsi_teams_id.team_number

                for laman in listahan:
                    stock_picking_db = self.env['etsi.pull_out.inventory']
                    stock_picking_db.create({
                        'job_number' : laman['job_number'], 
                        'etsi_product_name' : laman['etsi_product_name'],
                        'etsi_serial': laman['etsi_serial'],
                        'etsi_mac': laman['etsi_mac'],
                        'etsi_smart_card': laman['etsi_smart_card'],
                        'etsi_employee_in': laman['etsi_employee_in'],
                        'etsi_teams_id' : employee_id,
                        'etsi_status': 'received',
                        'etsi_receive_date_in': laman['etsi_receive_date_in'],
                        'transaction_number' : laman['name'],
                        'serial_type' : laman['serial_type'],
                        'employee_number' :laman['employee_number'],
                        'description' : laman['description']
                    })        
            else:
                raise ValidationError("Please fill up  Items to receive for pull-outs ")
        
        total = self.etsi_pullout_count + self.etsi_pullout_count_temp
        self.update({
            'state' : 'done',
            'status_field' : 'done',
            'min_date' : datetime.today(),
            'etsi_pullout_count' : total ,
        })
        
        count = self.env['etsi.pull_out.inventory'].search_count([('etsi_status','in', ('received','delivery'))])
        count2 = 0 
        
        # Apply the count per page
        for rec in self:
            for lines in rec.pullout_holder :
                count += 1
                count2 += 1

        self.update({
            'etsi_pullout_count_temp' :  count2
        })
            
    # Smart Button for Pull Outs
    @api.multi
    def get_all_pullouts(self):
        context = dict(self.env.context or {})
        context.update(create=False)
        return {
            'name': 'Subscriber Issuance',
            'res_model': 'etsi.pull_out.inventory',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'context': {'create':0},
        }
   
    # Button For return to Sky  
    @api.multi
    def receive_delivery_btn(self):
        picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))

        listahan = []
        count = 0

        for rec in self:
            for lines in rec.pullout_holder_return:
                if lines.for_delivery == True:
                    count += 1
            if count == 0:
                raise ValidationError("Please select at least one item to return to sky")
            else:
                pass

            search_name = self.env['stock.picking'].search([('name','=',rec.name)])
            picking_checker = self.env['stock.picking'].search([('picking_type_id.name','=', 'Pullout Return To Sky')])
            picking_checker2 = self.env['stock.picking.type'].search([('name', '=', 'Pullout Return To Sky')])
            stock_picking_db = self.env['stock.picking']

            product_lists = []
            product_serials = []

            # Update the date of delivery to sky cable of pull outs
            for plines_issued in rec.pullout_holder_return:
                if plines_issued.for_delivery == True:
                    product_lists.append(plines_issued.etsi_serial_product)
                    product_serials.append(plines_issued.etsi_serial_product)
                    issued_stats = self.env['pullout_picking_child_return'].search([])
                    inventory_stats = self.env['etsi.pull_out.inventory'].search([])

                    # To update the status of serials as returned from sky 
                    if product_serials:
                        Date = datetime.today()
                            
                        for searched_ids in inventory_stats:
                            if searched_ids.etsi_serial in product_serials:
                                searched_ids.update({'etsi_status': 'delivery',
                                'etsi_date_issued_in' : Date,
                                'transaction_number' : rec.name,
                                'status_field' : 'waiting',
                            })

            returned_pullouts = []

            for x in rec.pullout_holder_return:
                if x.for_delivery == True:
                    returned_pullouts.append(( 0, 0,{
                        'product_id': x.product_id,
                        'etsi_serial_product': x.etsi_serial_product, 
                        'etsi_mac_product': x.etsi_mac_product, 
                        'etsi_smart_card': x.etsi_smart_card,
                        'comp_date' : x.comp_date,
                        'quantity' : x.product_uom_qty,
                        'product_uom' : x.product_uom.id,
                        'product_uom_qty' : x.product_uom_qty, 
                        'issued': "returned",
                        'job_number' : x.job_number,
                        'move_id': x.id, 
                        'issued_field': "Returned",
                        'employee_number' : x.employee_number.id,
                        'is_damaged' : x.is_damaged,
                        'description' : x.description
                    }))

            self.update({
                'state' : 'draft',
                'pullout_holder_return' : False,
                'pullout_return_list' : returned_pullouts,  
                'status_field' : 'waiting',
            })
    
    # Validation for serial number for broadband within the table
    @api.constrains('pullout_holder')
    @api.onchange('pullout_holder')
    def _check_exist_serial_in_lineasd(self):
        exist_serial_list = []
        exist_mac_list = []
        exist_smart_card_list = []

        for search in self:
            for line in search.pullout_holder:
                if line.etsi_serial_product:
                    
                    if line.etsi_serial_product in exist_serial_list:
                        check = "Duplicate detected within the table \n Serial Number: {}".format(line.etsi_serial_product)
                        raise ValidationError(check)
                        # Raise Validation Error
                    exist_serial_list.append(line.etsi_serial_product)
            
                if line.etsi_mac_product:
                    if line.etsi_mac_product == False:
                        pass
                    elif line.etsi_mac_product in exist_mac_list:
                        check = "Duplicate detected within the table \n MAC ID : {}".format(line.etsi_mac_product)
                        raise ValidationError(check)
                    exist_mac_list.append(line.etsi_mac_product)
                
                if line.etsi_smart_card:
                    if line.etsi_smart_card in exist_smart_card_list:
                        check = "Duplicate detected within the table \n SMART CARD ID : {}".format(line.etsi_smart_card)
                        raise ValidationError(check)
                    exist_smart_card_list.append(line.etsi_smart_card) 

                if  line.etsi_serial_product == line.etsi_mac_product :
                    raise ValidationError(_('Serial ID is the same to MAC ID'))
               
        for fetch_serial_list in exist_serial_list:
            if fetch_serial_list in exist_mac_list:
                check = "Duplicate detected within the table serial and mac id is the same \n : {}".format(fetch_serial_list)
                raise ValidationError(check)
        
        for rec in self:
            for lines in rec.pullout_holder:
                if lines.serial_type == False and lines.etsi_serial_product:
                    if etsi_mac_product or etsi_smart_card == False:
                        raise ValidationError("PLEASE TYPE MAC OR SMART CARD ID")

    # Button For return to Sky  
    @api.multi
    def confirm_delivery_btn(self):
        picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
        listahan = []
        returned_pullouts = []
        rejected_pullouts = []
        
        # Checks if there stil remainingchckecked item
        for rec in self:
            counter = 0
            for item in rec.pullout_return_list:
                if item.for_delivery == True:
                    counter += 1
                    
        if counter == 0:
            raise ValidationError("Please select atleast one item to confirm delivery to sky") 
        
        for rec in self:
            counter = 0 
            for x in rec.pullout_return_list:
                if x.for_delivery == True:
                    if x.for_delivery == True:
                        returned_pullouts.append(( 0, 0,{
                            'product_id': x.product_id,
                            'etsi_serial_product': x.etsi_serial_product, 
                            'etsi_mac_product': x.etsi_mac_product, 
                            'etsi_smart_card': x.etsi_smart_card,
                            'comp_date' : x.comp_date,
                            'quantity' : x.product_uom_qty,
                            'product_uom' : x.product_uom.id,
                            'product_uom_qty' : x.product_uom_qty, 
                            'issued': "returned",
                            'job_number' : x.job_number,
                            'move_id': x.id, 
                            'issued_field': "Returned"
                        }))
                    
                    if x.for_delivery == False:
                        rejected_pullouts.append(({
                            'product_id': x.product_id,
                            'etsi_serial_product': x.etsi_serial_product, 
                            'etsi_mac_product': x.etsi_mac_product, 
                            'etsi_smart_card': x.etsi_smart_card,
                            'comp_date' : x.comp_date,
                            'quantity' : x.product_uom_qty,
                            'product_uom' : x.product_uom.id,
                            'product_uom_qty' : x.product_uom_qty, 
                            'issued': "received",
                            'job_number' : x.job_number,
                            'move_id': x.id, 
                            'issued_field': "Received"
                        }))
                        counter += 1
                    if counter == self.line_counter:
                        break
        
        for rec in self:
            search_name = self.env['stock.picking'].search([('name','=',rec.name)])
            picking_checker = self.env['stock.picking'].search([('picking_type_id.name','=', 'Pullout Return To Sky')])

            product_lists = []
            product_serials = []
            
            product_lists_rejected = []
            product_serials_rejected = []

            # if rec.picking_type_id.name == "Subscriber Return" or rec.picking_type_id.name == "Team Return":
            if rec.employee_for_delivery == False:
                raise ValidationError("Please input the team number for delivery")
            if rec.date_delivered == False:
                raise ValidationError("Please input the date delivered")
            if rec.received_by == False:
                raise ValidationError("Please input who received")
            else:

                for plines_issued in rec.pullout_return_list:
                    if plines_issued.for_delivery == True :
                        product_lists.append(plines_issued.etsi_serial_product)
                        product_serials.append(plines_issued.etsi_serial_product)
                        
                    if plines_issued.for_delivery == False :
                        product_lists_rejected.append(plines_issued.etsi_serial_product)
                        product_serials_rejected.append(plines_issued.etsi_serial_product)
                        
                issued_stats = self.env['pullout_picking_child_return'].search([])
                inventory_stats = self.env['etsi.pull_out.inventory'].search([])
                
                # To update the status of serials as returned from sky 
                if product_serials:
                    for searched_issueds in issued_stats:                
                        if searched_issueds.etsi_serial_product in product_lists:
                            searched_issueds.update({'issued': 'returned'})

                        for searched_ids in inventory_stats:
                            if searched_ids.etsi_serial in product_serials:
                                searched_ids.update({'etsi_status': 'returned',
                                'etsi_date_returned_in' : rec.date_delivered,
                                })

                # To update the status of rejected pullouts 
                if product_serials_rejected:
                    for searched_issueds_reject in issued_stats:
                        if searched_issueds_reject.etsi_serial_product in product_lists_rejected:
                            searched_issueds_reject.update({'issued': 'received'})

                        for searched_ids_reject in inventory_stats:
                            if searched_ids_reject.etsi_serial in product_serials_rejected:
                                searched_ids_reject.update({
                                    'etsi_status': 'received',
                                    'status_field' : 'draft'
                                })
        
        for rec in self:
            counter = 0
            for item in rec.pullout_return_list:
                if item.for_delivery == True:
                    counter += 1
                    
        # Finish the form
        self.update({
            'state' : 'done',
            'status_field' : 'done',
            'pullout_returned_quantity' : counter 
        })

class Validate_Pullout_Received_Child(models.Model):
    _name = 'pullout_picking_child'
    
    pullout_picking_child_connector = fields.Many2one('stock.picking')
     # Subscriber Form
    job_number = fields.Char("Job Order", required="True")
    subs_type = fields.Char("Type")
    comp_date = fields.Date("Pull Out Date", default=datetime.today(), required="True")
    form_num = fields.Char("Form Number")
    form_type = fields.Selection({
        ('a','Newly Installed'),
        ('b','Immediate')
    })
    serial_type = fields.Selection([('catv', 'CATV'),('modem', 'BROADBAND')], default='catv')
    etsi_teams_id = fields.Many2one('team.configuration', string="Team Number")
    product_id =  fields.Char('CPE Mat. Code') 
    quantity = fields.Float('Quantity')
    issued = fields.Selection([('received', 'On-hand'),('delivery', 'For Delivery'),('returned', 'Delivered')], string="Status", default='received', readonly=True)
    etsi_serial_product = fields.Char(string="Serial ID")
    etsi_mac_product = fields.Char(string="MAC ID")
    etsi_smart_card = fields.Char(string="Smart Card")
    active_ako = fields.Many2one('stock.picking')
    product_uom = fields.Many2one('product.uom', 'Unit of Measure', default=1)
    product_uom_qty = fields.Float('Quantity',default=1.0)
    active_name = fields.Char('Active Name')
    
    # Additional
    employee_number = fields.Many2one('hr.employee')
    is_damaged = fields.Boolean("Damaged")
    description = fields.Char("Description", required=True)

    # Validation for not both MAC and Serial
    @api.constrains('etsi_serial_product')
    @api.onchange('etsi_serial_product','etsi_mac_product','etsi_smart_card', 'serial_type')
    def onchange_transfer_pull_out_receive(self):
        # Validate Datas
        for rec in self:
            default_id = rec.etsi_teams_id

            # Search Count
            pm_search_sr_count = self.env['etsi.pull_out.inventory'].search_count([('etsi_serial','=', rec.etsi_serial_product)])
            pm_search_sr = self.env['etsi.pull_out.inventory'].search([('etsi_serial','=', rec.etsi_serial_product)])
            pm_search_mc = self.env['etsi.pull_out.inventory'].search([('etsi_mac','=', rec.etsi_mac_product)])
            pm_search_sc = self.env['etsi.pull_out.inventory'].search([('etsi_smart_card','=', rec.etsi_smart_card)])

            if rec.etsi_serial_product != False :
                if  pm_search_sr_count >= 1:
                        raise ValidationError("Serial already exists!")

                if rec.etsi_smart_card and rec.etsi_mac_product :
                    if rec.serial_type == 'catv':
                        self.update({'etsi_mac_product' : False})
                    else:
                        self.update({'etsi_smart_card' : False})

    @api.onchange('etsi_serial_product','etsi_mac_product','etsi_smart_card')
    def onchange_transfer_pull_out_returnasd(self):
        listahan = []
        # Validate Datas
        for rec in self:
            listahan.append(rec.etsi_serial_product)
        
    # Code for serial type
    @api.multi
    @api.onchange('serial_type')   
    def checker_onchange(self):
        # If transfer checker is checked
        for rec in self:
            search_name = self.env['stock.picking'].search([('name','=', rec.active_ako.name)])
            
            if rec.serial_type == 'catv':
                self.update({'etsi_mac_product' : False})
            else:
                self.update({'etsi_smart_card' : False})
    
class Validate_Pullout_Received_Child(models.Model):
    _name = 'pullout_picking_child_return'
    
    pullout_picking_child_connector_2 = fields.Many2one('stock.picking')
    # Pull Out Return Form
    for_delivery = fields.Boolean('Delivery')
    job_number = fields.Char("Job Order")
    job_number_related = fields.Char(related="job_number")
    subs_type = fields.Char("Type")
    comp_date = fields.Date("Pull Out Date", default=datetime.today())
    form_num = fields.Char("Form Number")
    form_type = fields.Selection({
        ('a','Newly Installed'),
        ('b','Immediate')
    })

    etsi_teams_id = fields.Char( string="Team Number")
    product_id =  fields.Char('CPE Mat. Code') 
    product_id_related = fields.Char(related='product_id')
    quantity = fields.Float('Quantity')
    issued = fields.Selection([('received', 'On-hand'),('delivery', 'Delivered'),('returned', 'Returned'),('damaged', 'Damaged')], string="Status", default='delivery', readonly=True)
    etsi_serial_product = fields.Char(string="Serial ID")
    etsi_mac_product = fields.Char(string="MAC ID")
    etsi_smart_card = fields.Char(string="Smart Card")
    active_ako = fields.Char("Active Ako ")
    product_uom = fields.Many2one('product.uom', 'Unit of Measure', default= 1)
    product_uom_qty = fields.Float('Quantity',default=1.0)
    active_name = fields.Char('Active Name')

    # Additional
    employee_number = fields.Many2one('hr.employee')
    is_damaged = fields.Boolean("Damaged")
    description = fields.Char("Description")
    
    @api.onchange('etsi_serial_product','etsi_mac_product','etsi_smart_card')
    def onchange_transfer_pull_out_return(self):
        # Validate Datas
        for rec in self:
            default_id = rec.etsi_teams_id

            # search available products - stock.move model
            pm_search_sr = self.env['etsi.pull_out.inventory'].search([('etsi_serial','=', rec.etsi_serial_product)])
            pm_search_mc = self.env['etsi.pull_out.inventory'].search([('etsi_mac','=', rec.etsi_mac_product)])
            pm_search_sc = self.env['etsi.pull_out.inventory'].search([('etsi_smart_card','=', rec.etsi_smart_card)])
            
            # Valued data only passes
            if rec.etsi_serial_product != False or rec.etsi_mac_product != False or rec.etsi_smart_card != False:
                # Checks if search is true
                if pm_search_sr:
                    if rec.etsi_serial_product:
                        # Validation for issued status
                        for ser in pm_search_sr:
                            if ser.etsi_status == "delivery":
                                raise ValidationError("This Product is already on delivery!")
                                rec.product_id = False
                                rec.etsi_serial_product =  False
                                rec.etsi_mac_product = False
                                rec.etsi_smart_card = False
                                rec.issued = False
                                rec.quantity = False
                                rec.product_uom = False
                            if ser.etsi_status == "returned":
                                raise ValidationError("Product is already returned to Sky!")
                            
                            # Auto fill statements
                            rec.job_number = ser.job_number
                            rec.product_id = ser.etsi_product_name
                            rec.etsi_mac_product = ser.etsi_mac
                            rec.etsi_smart_card = ser.etsi_smart_card
                            rec.quantity = 1.00

                            # rec.product_uom = 21
                            rec.etsi_teams_id = ser.etsi_teams_id
                            break
                else:
                    raise ValidationError("Serial not found in the database")

class Validate_Pullout_Return_List(models.Model):
    _name = 'pullout_picking_child_return_list'

    pullout_return_list_connector = fields.Many2one('stock.picking')

    # Pull Out Return Form
    for_delivery = fields.Boolean('Delivery', default = True)
    job_number = fields.Char("Job Order")
    job_number_related = fields.Char(related="job_number")
    subs_type = fields.Char("Type")
    comp_date = fields.Date("Pull Out Date", default=datetime.today())
    form_num = fields.Char("Form Number")
    form_type = fields.Selection({
        ('a','Newly Installed'),
        ('b','Immediate')
    })
    etsi_teams_id = fields.Char( string="Team Number")
    product_id =  fields.Char('CPE Mat. Code') 
    product_id_related = fields.Char(related='product_id')
    quantity = fields.Float('Quantity')
    issued = fields.Selection([('received', 'On-hand'),('delivery', 'Delivery'),('returned', 'Returned'),('damaged', 'Damaged')], string="Status", default='delivery', readonly=True)
    etsi_serial_product = fields.Char(string="Serial ID")
    etsi_mac_product = fields.Char(string="MAC ID")
    etsi_smart_card = fields.Char(string="Smart Card")
    active_ako = fields.Char("Active Ako ")
    product_uom = fields.Many2one('product.uom', 'Unit of Measure', default= 1)
    product_uom_qty = fields.Float('Quantity',default=1.0)
    active_name = fields.Char('Active Name')

    # Additional
    employee_number = fields.Many2one('hr.employee')
    is_damaged = fields.Boolean("Damaged")
    description = fields.Char("Description")
    
class Etsi_Pullout_Inventory(models.Model):
    _name = 'etsi.pull_out.inventory'

    @api.multi 
    def _get_count_list(self):
        data_obj = self.env['etsi.pull_out.inventory']
        for data in self:       
            list_data  = data_obj.search([()])
            data.example_count = len(list_data)

    etsi_serial = fields.Char(string="Serial ID")
    etsi_mac = fields.Char(string="MAC ID")
    etsi_smart_card = fields.Char(string="Smart Card")
    etsi_status = fields.Selection([('received', 'Received'),('delivery', 'Delivery'),('returned', 'Returned'), ('damaged', 'Damaged')], string="Status", default='delivery', readonly=True)
    etsi_product_id = fields.Many2one('product.product',string="Product")
    etsi_product_name = fields.Char(string="Product")
    etsi_teams_id = fields.Char('Team')
    type_checker = fields.Selection(related='etsi_product_id.internal_ref_name')
    etsi_receive_date_in = fields.Date(string="Date Received",default = datetime.today())
    etsi_date_issued_in = fields.Date(string="Date of Delivery" )
    etsi_date_returned_in = fields.Date(string="Date Returned")
    etsi_date_received_in = fields.Date(string="Date Issued", default = datetime.today())
    etsi_team_in = fields.Char(string="Team")
    etsi_punched_date_in = fields.Date("Punch Time", default = datetime.today())
    etsi_employee_in = fields.Char("Employee")
    job_number =  fields.Char('Job Order')
    transaction_number = fields.Char('Transaction Number')
    status_field = fields.Selection([('draft', 'Draft'),('waiting', 'Waiting For Delivery Team'),('done', 'Done')], default='draft')
    serial_type = fields.Selection([('catv', 'CATV'),('modem', 'BROADBAND')], default='catv')
    
    # Additional
    employee_number = fields.Many2one('hr.employee')
    is_damaged = fields.Boolean("Damaged")
    description = fields.Char("Description", required=True)