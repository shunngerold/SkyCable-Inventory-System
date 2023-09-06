from odoo import api, fields, models, _
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from odoo.exceptions import ValidationError, UserError

class Validate_Subscriber_Issuance(models.Model):
    _inherit = 'stock.picking'
    
    # Subscriber Issuance Form Field
    job_number = fields.Char("Job Order")
    subs_type = fields.Char("Type")
    comp_date = fields.Date("Completion Date", default=datetime.today())
    form_num = fields.Text("Form Number")
    form_type = fields.Selection({
        ('a','Newly Installed'),
        ('b','Immediate')
    })
    
    # One2many for items that will be issued 
    subs_issue = fields.One2many('subscriber_issuance_child','subs_issuance_connector')
    drops_issue = fields.One2many('drops_issuance_child','drops_issuance_connector')


    # Validation for serial number within the table 
    @api.constrains('subs_issue')
    @api.onchange('subs_issue')
    def _check_exist_serial_in_line_subs(self):

        exist_serial_list = []
        exist_mac_list = []
        exist_smart_card_list = []

        count = 0
        for search in self:
            for line in search.subs_issue:
                if line.etsi_serial_product == False:
                    raise ValidationError(_('Serial ID can not be blank'))
                if line.etsi_serial_product:
                    
                    if line.etsi_serial_product in exist_serial_list:
                        check = "Duplicate detected within the table \n Serial Number: {}".format(line.etsi_serial_product)
                        raise ValidationError(check) # Raise Validation Error
                        
                    exist_serial_list.append(line.etsi_serial_product)
                    
    
    # When Validate button is clicked
    @api.multi
    def do_new_transfer(self):
        if self.teller == 'subscriber':
            subs_list = []
            drop_list = []
            for rec in self:
                search_name = self.env['stock.picking'].search([('name','=',rec.name)])
                picking_checker = self.env['stock.picking'].search([('picking_type_id.name','=','Subscriber Issuance')])
                search_job_number = self.env['stock.drops.issuance'].search([])

                for x in rec.subs_issue:
                    subs_list.append((
                        0, 0, {
                            'name':x.product_id.product_tmpl_id.name,
                            'product_id': x.product_id_related.id, 
                            'product_uom_qty' : x.product_uom_qty, 
                            'product_uom' : x.product_uom_related.id, # Unit of measure 
                            'move_id': x.id, 
                            'issued_field': "Used",
                            'etsi_serials_field': x.etsi_serial_product, 
                            'etsi_mac_field': x.etsi_mac_product, 
                            'etsi_smart_card_field': x.etsi_smart_card,
                            'state' : 'draft',
                            'location_id' : rec.location_id,
                            'location_dest_id' : rec.location_dest_id,
                            'picking_type_id': rec.picking_type_id
                        }))

            inventory_stats = self.env['etsi.inventory'].search([])
            ids = []
            listahan = []
            for rec in self:
                for item in rec.drops_issue:
                    ids.append(item.product_id.id)
            
            for laman in inventory_stats:
                if laman.type_checker_02 == 'drops':
                    listahan.append(laman.etsi_product_id.id)
                    print(laman.etsi_product_id.id, "MGA ID sa etsi.inventory ")
                
            for idsss in ids:
                if idsss not in listahan:
                    raise ValidationError("DROP IS NOT YET ISSUED TO TEAM LOCATION")
                else:
                    print(" NA ISSUE NAMAN LAHAT ")         
                
            for x in rec.drops_issue:
                drop_list.append((
                    0, 0, {
                        'name': x.product_id.product_tmpl_id.name,
                        'product_id': x.product_id, 
                        'product_uom_qty' : x.clicksolf_quantity, 
                        'product_uom' :x.product_uom.id, # Unit of measure 
                        'move_id': 1, 
                        'issued_field': "Used",
                        # 'etsi_serials_field': x.etsi_serial_product, 
                        # 'etsi_mac_field': x.etsi_mac_product, 
                        # 'etsi_smart_card_field': x.etsi_smart_card,
                        'state' : 'draft',
                        'location_id' : rec.location_id,
                        'location_dest_id' : rec.location_dest_id,
                        'picking_type_id': rec.picking_type_id
                    }))
            
        etsi = []
        # Loop trough all the items of drop issuance one2many   
        inventory_stats = self.env['etsi.inventory'].search([('type_checker_02', '=' ,'drops')])
        
        for item in inventory_stats:
            etsi.append(item.etsi_product_id.id)
            etsi.append(item.etsi_team_in.id)
        
        for laman in self.drops_issue:
            if laman.product_id.id in etsi: 
                print("FOUND", laman.product_id.name)
                        
                
            
            # CHANGE STATUS FROM NEW TO PROCESSED FOR THAT JOB_ORDER NUMBER
                jo_list = []
                
                for jo in rec.drops_issue:
                    
                    jo_list.append(jo.job_number)
                    print("1")
                
                if jo_list:
                    print("2")
                    
                    for laman in search_job_number:
                    
                        print(laman.callid, "JOB ORDER NUMBER")
                        print("3")
                        if laman.callid in jo_list:
                            
                            print("4")
                            print(laman.callid," CALL ID ")
                            
                            
                            laman.write({'stats': 'done'})
                        
                
            # self.update({
            #     # 'move_lines': subs_list,drop_list
            #     'move_lines': subs_list,
                
               
            # })

        
        # Subtract quantity for etsi.inventory
        inventory_stats = self.env['etsi.inventory'].search([('type_checker_02', '=' ,'drops')])
        picking_id_checker = self.env['stock.picking'].search([('name', '=', self.name)])
        
        quantity = []
        # for count in self.drops_issue:
        #     quantity.append(count.product_id.id)
        #     quantity.append(count.clicksolf_team.id)
        
        
        # for ets in inventory_stats:
        #     quantity.append(ets.product_id)
            
        
        total = 0
        for qty in self.drops_issue:
            for item in inventory_stats:
                if item.etsi_product_id.id == qty.product_id.id and item.etsi_team_in.id == qty.clicksolf_team.id:
                    print("ETSI PRODUCT ID",item.etsi_product_id.id )
                    print("QTY PRODUCT ID",qty.product_id.id )
                    print(item.etsi_product_quantity, "QUANTITY SA ETSI")
                    print(qty.clicksolf_quantity, "CLICK SOFT QUANTITY")
                    
                    print("NA MINUS NA QTY", item.etsi_product_quantity - qty.clicksolf_quantity  )
                    if qty.clicksolf_quantity > item.etsi_product_quantity:
                        check = "Drops quantity is more than the issued product: {}".format(item.etsi_product_id.name)
                        raise ValidationError(check)
                    
                        
                        
                    total =  item.etsi_product_quantity - qty.clicksolf_quantity 
                    print("TOTAL", total)

                    item.update({'etsi_product_quantity' : total})
                    
                    neg_quantity = qty.clicksolf_quantity * -1
                    
                    # etsi.inventory.history
                    item.write({'etsi_history_lines': [(0,0, {'etsi_operation':'Drops Issuance','etsi_transaction_num':picking_id_checker.id,'etsi_action_date': datetime.today(),'etsi_status':'Used','etsi_employee':self.env.user.id,'etsi_teams':qty.clicksolf_team.id,'etsi_history_quantity': neg_quantity,'etsi_transaction_description':'Team to Partner Location ('  + (qty.job_number) +")"})]})
        
                
                # elif item.etsi_product_id.id == qty.product_id.id and item.etsi_team_in.id != qty.clicksolf_team.id:
                #     print("ETSI PRODUCT ID ELIF",item.etsi_product_id.id )
                #     print("QTY PRODUCT ID ELIF",qty.product_id.id )
                #     check = "Drops is not yet issued  : {}".format(item.etsi_product_id.name)
                #     raise ValidationError(check)
        
        if self.teller == 'subscriber':
            

            self.update({
                # 'move_lines': subs_list,drop_list
                'move_lines':  subs_list
            })
        if self.teller == 'subscriber':
            
        
            self.update({
                # 'move_lines': subs_list,drop_list
                'move_lines':  drop_list
            })
        # Code for updating the status of products as issued 
        
        res = super(Validate_Subscriber_Issuance, self).do_new_transfer()

        for rec in self:
            if rec.teller == 'subscriber':
                picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
                picking_id_checker = self.env['stock.picking'].search([('name', '=', self.name)])

                search_name = self.env['stock.picking'].search([('name','=',rec.name)])
                picking_checker = self.env['stock.picking'].search([('picking_type_id.name','=', 'Subscriber Issuance')])
                picking_checker2 = self.env['stock.picking.type'].search([('name', '=', 'Subscriber Issuance')])
                stock_picking_db = self.search([])

                self.update({
                    'state' : 'done'
                })
                
                # list To Update the status 
                count = 0
                counter = []
                counter2 = []
                product_lists = []
                product_serials = []
                product_serials_issued= []
                product_lists_issued = []
                serial_trans = []
                serial_store = []
                final= []
                final_info = []
                final_ids = []

                # if rec.picking_type_id.name == "Subscriber Return" or rec.picking_type_id.name == "Team Return":
                for plines_issued in rec.subs_issue:
                    product_serials_issued.append(plines_issued.etsi_serial_product)
                    product_lists_issued.append(plines_issued.product_id)

                for item in product_serials_issued:
                    final.append(item)

                for items_ids in product_lists_issued:
                    final_ids.append(items_ids.id)

                issued_stats = self.env['stock.move'].search([('issued_field','=','Deployed')])
                inventory_stats = self.env['etsi.inventory'].search([])
                
                if final and final_ids:
                    for plines_issued in rec.subs_issue:
                        trans_float_data = self.env['stock.transfer.team.return'].search([('etsi_serial_product','=', plines_issued.etsi_serial_product)]) # fetch temp data
                        serial_store.append(plines_issued.etsi_serial_product) # store serials for validation
                        
                        for trans in trans_float_data:
                            if trans: # get true data only
                                invento = self.env['etsi.inventory'].search([('etsi_serial','=', plines_issued.etsi_serial_product)], limit=1)
                                serial_trans.append(trans.etsi_serial_product) # store serial in 

                                # check if installed item is available in transfer
                                if trans.etsi_serial_product in final and trans.issued == 'Waiting' and trans.transfer_checker == True and trans.return_checker == False:
                                    trans_move = self.env['stock.move'].search([('etsi_serials_field', '=', trans.etsi_serial_product), ('issued_field','=','Deployed')])

                                    trans.update({ # Update existing floating data
                                        'issued': "Done",
                                        'prod_stat': "Done",
                                        'return_checker': True,
                                        'installed': True,
                                    })

                                    for move in trans_move: # update stock.move
                                        if move.etsi_serials_field: # get true data
                                            counter.append(move.id) # store ids for validation
                                            counter_filtered = list(set(counter)) # remove duplicates
                                        for x in counter_filtered: # fetch non-duplicate data
                                            trans_move2 = self.env['stock.move'].search([('etsi_serials_field', '=', trans.etsi_serial_product),('id', '=', x),('issued_field','=','Deployed')])
                                            trans_move2.update({'picking_id': trans.source.id}) # Replace team_issuance ref number
                                            trans_move2.update({'issued_field': 'Used'}) # Update product status - to used

                                    for inventory in inventory_stats: # update etsi.inventory - team number
                                        if inventory.etsi_serial == trans.etsi_serial_product:
                                            inventory.update({'etsi_team_in': trans.team_num_to.id}) # update team_number
                                            inventory.update({'etsi_status': 'used'}) # update product status 
                                            
                                            # update history
                                            inventory.write({'etsi_history_lines': [(0,0, {'etsi_operation':'Transfer (Subscriber Issuance)','etsi_transaction_num':picking_id_checker.id,'etsi_action_date': datetime.today(),'etsi_status':'Used','etsi_employee':self.env.user.id,'etsi_teams': trans.team_num_to.id,'etsi_history_quantity': 1,'etsi_transaction_description':'Team to Partner Location'})]})
                                
                    
        return res

    # Code for checking what form the user is currently in
    @api.model
    def default_get(self, fields):
        res = super(Validate_Subscriber_Issuance, self).default_get(fields)

        data_obj = self.env['stock.picking']
        for data in self:       
            list_data = data_obj.search([()])
            data.etsi_subscriber_issuance = len(list_data)  

        if 'picking_type_id' in res:
            picking_type_id = res['picking_type_id']
            
            self.env['hr.employee.category'].search([ ('default_emp_category', '=', True)]).ids

            search = self.search([('picking_type_id','=', picking_type_id)], limit=1)
            names = self.env['hr.employee.category'].search([ ('default_emp_category', '=', True)]).name

            pm_search_sr = self.env['stock.picking.type'].search([('id','=', picking_type_id)])
            
            data_obj    = self.env['stock.picking']
            for data in self:       
                list_data   = data_obj.search([])
                data.example_count = len(list_data)

            if pm_search_sr.name == 'Subscriber Issuance':
                res['teller'] = 'subscriber'
            if pm_search_sr.name == 'Team Issuance':
                res['teller'] = 'others'
            if pm_search_sr.name == 'Team Return':
                res['teller'] = 'return'
            if pm_search_sr.name == 'Damage Location':
                res['teller'] = 'damage'
            if pm_search_sr.name == 'Pullout Receive':
                res['teller'] = 'pull-out'
            if pm_search_sr.name == 'Pullout Return To Sky':
                res['teller'] = 'pull-out-return'
        return res

class Validate_Subscriber_Issuance_Child(models.Model):
    _name = 'subscriber_issuance_child'

    subs_issuance_connector = fields.Many2one('stock.picking')
     # Subscriber Form
    job_number = fields.Char("Job Order")
    subs_type = fields.Char("Type")
    comp_date = fields.Date("Completion Date", default=datetime.today())
    form_num = fields.Char("Form Number")
    form_type = fields.Selection({
        ('a','Newly Installed'),
        ('b','Immediate')
    })
    product_id =  fields.Many2one('product.product', required="True") 
    product_id_related =  fields.Many2one('product.product', related="product_id") 
    quantity = fields.Float('Quantity')
    issued = fields.Char(string="Status",default="Used")
    etsi_serial_product = fields.Char(string="Serial ID")
    etsi_mac_product = fields.Char(string="MAC ID")
    etsi_mac_product_related = fields.Char(related="etsi_mac_product")
    etsi_smart_card = fields.Char(string="Smart Card")
    etsi_smart_card_related =  fields.Char(related='etsi_smart_card')
    active_ako = fields.Char("Active Ako ")
    product_uom = fields.Many2one(
        'product.uom', 'Unit of Measure')
    product_uom_related = fields.Many2one(
        'product.uom', related="product_uom")
    product_uom_qty = fields.Float('Quantity',default=1.0)
    active_name = fields.Char('Active Name')
    trans_checker = fields.Boolean("Transfered")
    team = fields.Many2one('team.configuration', string="Team")
    teams_to = fields.Many2one('team.configuration', string="Team Duplicate", related="team")

    @api.onchange('etsi_serial_product','etsi_mac_product','etsi_smart_card')
    def onchange_transfer(self):
        # Validate Datas

        recommend = []
        for rec in self:
            # search available products - stock.move model
            pm_search_sr = self.env['stock.move'].search([('etsi_serials_field','=', rec.etsi_serial_product)])
            pm_search_mc = self.env['stock.move'].search([('etsi_mac_field','=', rec.etsi_mac_product)])
            pm_search_sc = self.env['stock.move'].search([('etsi_smart_card_field','=', rec.etsi_smart_card)])
            
            # Check the etsi status
            pm_search_sr_id = self.env['etsi.inventory'].search([('etsi_serial','=', rec.etsi_serial_product)])
            trans_float_data = self.env['stock.transfer.team.return'].search([('etsi_serial_product','=', rec.etsi_serial_product)]) # fetch temp data
            
            # Lists
            # search available products - stock.picking.return.list.holder model        
            # Valued data only passes
            if rec.etsi_serial_product != False or rec.etsi_mac_product != False or rec.etsi_smart_card != False:
                
                if rec.etsi_serial_product != False or rec.etsi_mac_product != False or rec.etsi_smart_card != False:
                
                    if rec.etsi_serial_product :
                        for ser in pm_search_sr_id:

                            if ser.etsi_status == "available":
                                raise ValidationError("This Product is not yet issued!")
                            if ser.etsi_status == "used":
                                raise ValidationError("This Product is already issued!")
                        
                # Check if data inputted is available
                # MAC ID
                if rec.etsi_mac_product:
                    # Validation for issued status
                    for mac in pm_search_mc:
                        # Auto fill statements
                        rec.product_id = mac.product_id.id
                        rec.etsi_serial_product = mac.etsi_serials_field
                        rec.etsi_smart_card = mac.etsi_smart_card_field
                        rec.issued = "Used"
                        rec.quantity = 1.00
                        rec.product_uom = 1
                        break
                
                # Smart Card
                if rec.etsi_smart_card:
                    # Validation for issued status
                    for scard in pm_search_sc:
                        # Auto fill statements
                        rec.product_id = scard.product_id.id
                        rec.etsi_mac_product = scard.etsi_mac_field
                        rec.etsi_serial_product = scard.etsi_serials_field
                        rec.issued = "Used"
                        rec.quantity = 1.00
                        rec.product_uom = 1
                        break
                        
                # Serial Number
                if rec.etsi_serial_product:
                    # Validation for issued status
                    for ser in pm_search_sr:

                        if ser.issued_field == "Available":
                            raise ValidationError("This Product is not yet issued!")

                        if ser.issued_field != "Deployed":
                            raise ValidationError("This Product is already issued!")

                        if trans_float_data:
                            for trans in trans_float_data: # fetch temp data
                                # Auto fill statements
                                rec.product_id = ser.product_id.id
                                rec.etsi_mac_product = ser.etsi_mac_field
                                rec.etsi_smart_card = ser.etsi_smart_card_field
                                rec.issued = "Used"
                                rec.quantity = 1.00
                                rec.product_uom = 1
                                rec.team = trans_float_data.team_num_to.id
                                break
                        else:
                            # Auto fill statements
                            rec.product_id = ser.product_id.id
                            rec.etsi_mac_product = ser.etsi_mac_field
                            rec.etsi_smart_card = ser.etsi_smart_card_field
                            rec.issued = "Used"
                            rec.quantity = 1.00
                            rec.product_uom = 1
                            rec.team = pm_search_sr_id.etsi_team_in.id
                            break
    

        

class Subscriber_issuance(models.Model):
    _inherit = 'stock.move'

    # Add aditional fields for move_lines
    subs_issuance_connector = fields.Many2one('stock.picking')
     # Subscriber Form
    job_number = fields.Char("Job Order")
    subs_type = fields.Char("Type")
    comp_date = fields.Date("Completion Date", default=datetime.today())
    form_num = fields.Char("Form Number")
    form_type = fields.Selection({
        ('a','Newly Installed'),
        ('b','Immediate')
    })


# FOR DROPS NEW REQUIREMENTS

class Drops_issuance(models.Model):
    _name = 'drops_issuance_child'
    
    drops_issuance_connector = fields.Many2one('stock.picking')
    job_number = fields.Char("Job Order")
    product_id =  fields.Many2one('product.product', required="True") 
    product_description = fields.Char('Description')
    product_clicksolf_code = fields.Char("Code")
    clicksolf_quantity = fields.Integer("Quantity")
    clicksolf_team = fields.Many2one('team.configuration')
    product_uom = fields.Many2one('product.uom', 'Unit of Measure')
    

class ValidationProcess(models.TransientModel):
    _inherit ='stock.immediate.transfer'
        # bypass mark as to do since it was remove
    @api.multi
    def process(self):
        self.ensure_one()
        # If still in draft => confirm and assign
        if self.pick_id.state == 'draft':
            self.pick_id.action_confirm()
            if self.pick_id.state != 'assigned':
                self.pick_id.action_assign()
                if self.pick_id.state != 'assigned':
                    raise UserError(_("Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
        for pack in self.pick_id.pack_operation_ids:
            if pack.product_qty > 0:
                pack.write({'qty_done': pack.product_qty})
            else:
                pack.unlink()
        return self.pick_id.do_transfer()