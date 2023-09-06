from odoo import api, fields, models, _
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError, UserError

class Validate_Team_Return(models.Model):
    _inherit = 'stock.picking'

    # picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
    teller = fields.Selection([('return', 'Return'),('damage', 'Damage'),('others', 'Others'),('subscriber', 'Subscriber'),('pull-out', 'Pullout Receive'),('pull-out-return', 'Pullout Return')], default='others')
    source = fields.Many2one('stock.picking', domain="[('picking_type_id.name','=', 'Team Issuance')]", string="Source Document")
    transfered_item = fields.Many2one("etsi.inventory")
    product_stats = fields.Selection([
        ('damage','Damaged'),
        ('return','Returned')
    ], string="Product status")
    remarks = fields.Text("Remarks")
    # One2many to list all items
    return_list = fields.One2many('stock.picking.return.list','return_list_connector')
    # Returned Items list 
    return_items = fields.One2many('stock.picking.returned.item.list','return_item_connector')
    # Damaged Items List 
    damaged_items =  fields.One2many('stock.picking.damaged.item.list','damaged_item_connector')

    @api.model
    def default_get(self, fields):
        res = super(Validate_Team_Return, self).default_get(fields)

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
    
    # Auto fill of return_list_code
    @api.onchange('source')
    def change_return_list(self):
        picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
        listahan = []
        for rec in self:
            search_name = self.env['stock.picking'].search([('name','=',rec.name)])
            picking_checker = self.env['stock.picking'].search([('picking_type_id.name','=', 'Team Return')])
            
            search_first = self.env['stock.picking'].search([('name','=',rec.source.name)])

            for item in search_first:
                teams_id = item.etsi_teams_id.id
                search_first2 = self.env['stock.move'].search([])
                for x in search_first2:
                    if x.picking_id.name == rec.source.name:
                        if  x.issued_field == 'Deployed' :
                            # listahan.append({'serial':x.etsi_serials_field, 'mac_id': x.etsi_mac_field })
                            listahan.append((
                            0, 0, {
                                'product_id': x.product_id.id, 
                                'quantity' : x.product_uom_qty, 
                                # Unit of measure 
                                'product_uom' : x.product_uom.id,
                                'move_id': x.id, 
                                'issued': x.issued_field,
                                'etsi_serial_product': x.etsi_serials_field, 
                                'etsi_mac_product': x.etsi_mac_field, 
                                'etsi_smart_card': x.etsi_smart_card_field,
                                'issued_field': x.issued_field,
                                'subscriber' : x.subscriber_field.id,
                                'state' : 'draft',
                                'active_ako' : x.picking_id.id,
                                'active_name' : rec.name,
                                'teams': rec.etsi_teams_id.id
                            }
                            ))
                            self.update({'etsi_teams_id' : teams_id })

        # Update the one2many table
            self.update({'return_list': listahan})

# Transient Model to hold all that will be returned(same as product_return_moves)
class Return_list_holder(models.TransientModel):
    _name = 'stock.picking.return.list.holder'
    
    # One2many to list all items
    return_list_move_holder = fields.One2many('stock.picking.return.list_2','return_list_moves_connector_2')
    damage_list_ids = fields.One2many("stock.picking.damage.list", "damage_list_id")
    transfer_list_ids = fields.One2many("stock.picking.transfer.list", "transfer_list_id")
    # installed_list_move_holder =  fields.One2many('stock.picking.return.list_3','return_list_moves_connector_3')

    # Action na pag save 
    @api.multi
    def return_btn(self):
        picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
        issued_stats = self.env['stock.move'].search([])
        inventory_stats = self.env['etsi.inventory'].search([])

        # Pick up the return picking_type_id for return
        picking_type_id = picking.picking_type_id.id 
        # List for team return
        team_return = []
        product_lists = []
        product_serials = []
        # list for damaged item
        team_return_damaged = []
        # list for transfered items
        team_return_transfer = []

        # Return
        if self.return_list_move_holder:
            picking_checker_return = self.env['stock.picking.type'].search([('name', '=', 'Team Return')])

            for line_ret in self.return_list_move_holder:
                team_return.append({
                    'name':line_ret.product_id.product_tmpl_id.name,
                    'product_id': line_ret.product_id.id,
                    'etsi_serials_field': line_ret.etsi_serial_product,
                    'etsi_mac_field': line_ret.etsi_mac_product,
                    'etsi_smart_card_field': line_ret.etsi_smart_card,
                    'etsi_serial_product' : line_ret.etsi_serial_product,
                    'etsi_mac_product' : line_ret.etsi_mac_product,
                    'etsi_smart_card' : line_ret.etsi_smart_card,
                    'issued' : "Available",
                    'issued_field': "Available",
                    'product_uom': line_ret.product_id.product_tmpl_id.uom_id.id,
                    'product_uom_qty' : line_ret.quantity,
                    'quantity': line_ret.quantity, 
                    'move_id': line_ret.id,
                    'location_id' : picking_checker_return.default_location_src_id,
                    'location_dest_id' : picking_checker_return.default_location_dest_id,
                    'picking_type_id': picking_checker_return.id,
                    'teams' : line_ret.teams                }) 
            
        # Damaged
        if self.damage_list_ids:
            picking_checker_damaged = self.env['stock.picking.type'].search([('name', '=', 'Damage Location')])
            for line_dmg in self.damage_list_ids:
                team_return_damaged.append({
                    'name':line_dmg.product_id.product_tmpl_id.name,
                    'product_id': line_dmg.product_id.id,
                    'etsi_serials_field': line_dmg.etsi_serial_product,
                    'etsi_mac_field': line_dmg.etsi_mac_product,
                    'etsi_smart_card_field': line_dmg.etsi_smart_card,
                    'etsi_serial_product' : line_dmg.etsi_serial_product,
                    'etsi_mac_product' : line_dmg.etsi_mac_product,
                    'etsi_smart_card' : line_dmg.etsi_smart_card,
                    'dmg_type': line_dmg.dmg_type,
                    'issued_field': "Damaged",
                    'issued' : "Damaged", 
                    'product_uom': line_dmg.product_id.product_tmpl_id.uom_id.id,
                    'product_uom_qty' : line_dmg.quantity, 
                    'move_id': line_dmg.id,
                    'quantity': line_dmg.quantity, 
                    'location_id' : picking_checker_damaged.default_location_src_id,
                    'location_dest_id' : picking_checker_damaged.default_location_dest_id,
                    'picking_type_id': picking_checker_damaged.id,
                    'teams_from_damage' : line_dmg.teams_from_damage,
                    'active_name' : picking.id
                })
        
        # Transfer declaration / process
        if self.transfer_list_ids:
            for line_trans in self.transfer_list_ids:
                team_return_transfer.append({
                    'name':line_trans.product_id.product_tmpl_id.name,
                    'product_id': line_trans.product_id.id,
                    'etsi_serials_field': line_trans.etsi_serial_product,
                    'etsi_mac_field': line_trans.etsi_mac_product,
                    'etsi_smart_card_field': line_trans.etsi_smart_card,
                    'issued_field': "Return",
                    'product_uom': line_trans.product_id.product_tmpl_id.uom_id.id,
                    'quantity': line_trans.quantity,
                    'teams_from': line_trans.teams_from.id,
                    'teams_to': line_trans.teams_to.id,
                    'location_id' : 1,
                    'location_dest_id' : 2,
                    'picking_type_id': 6
                })       
        
        for rec in self:
            # Normal Return
            if team_return:
                picking.update({
                    'state' : 'done',
                    # 'picking_type_id': picking_type_id,
                    'move_lines': team_return,
                    'return_items' : team_return,
                    'status_field' :  'done',
                    'location_id': picking.picking_type_id.default_location_src_id.id,
                    'location_dest_id': picking.picking_type_id.default_location_dest_id.id,
                })
            
                for plines in rec.return_list_move_holder:
                    if picking.etsi_teams_id.id == plines.teams.id:
                        product_lists.append(plines.product_id)
                        product_serials.append(plines.etsi_serial_product)
                
                # For Normal Return
                if product_lists and product_serials:
                    for issued_ids in issued_stats:
                        if issued_ids.etsi_serials_field in product_serials: 
                            issued_ids.update({'issued_field': 'Available'})
            
                    for searched_ids in inventory_stats: # Normal Return - etsi_inventory
                        if searched_ids.etsi_product_id in product_lists: 
                            if searched_ids.etsi_serial in product_serials: 
                                date_returned = datetime.today()
                                searched_ids.update({'etsi_status': 'available'})
                                searched_ids.update({'etsi_date_returned_in': date_returned})
                                searched_ids.update({'etsi_team_in': False})
                                # update history
                                searched_ids.write({'etsi_history_lines': [(0,0, {'etsi_operation':'Team Return','etsi_transaction_num':picking.id,'etsi_action_date': datetime.today(),'etsi_status':'Available','etsi_employee':self.env.user.id,'etsi_teams':picking.etsi_teams_id.id,'etsi_history_quantity': 1,'etsi_transaction_description':'Team Location to Warehouse'})]})
            
            # Damage Transaction
            if team_return_damaged: 
                issued_stats = self.env['stock.move'].search([])
                inventory_stats = self.env['etsi.inventory'].search([]) 
                picking_checker2 = self.env['stock.picking.type'].search([('name', '=', 'Damage Location')])
                
                final_return_list_damaged = []

                for line_return_damage in team_return_damaged:
                    final_return_list_damaged.append((0,0,line_return_damage))
            
                # Appends the list for teams selected
                team_lst = []
                for team_line in picking.etsi_teams_line_ids:
                    team_res = {
                        'team_members_lines': team_line.team_members_lines.id,
                        'etsi_teams_replace': team_line.etsi_teams_replace.id,
                        'etsi_teams_temporary': team_line.etsi_teams_temporary,
                    }
                    team_lst.append(team_res)

                team_new_list = []
                for team_line2 in team_lst:
                    team_new_list.append((0,0,team_line2))

                stock_picking_db = self.env['stock.picking']
                return_damaged_function = stock_picking_db.create({
                        'etsi_team_issuance_id': picking.id,
                        'picking_type_id': picking_checker2.id,
                        'origin': picking.name,
                        'move_lines':final_return_list_damaged,
                        # Damaged items
                        'damaged_items' : final_return_list_damaged, 
                        'location_id': picking_checker2.default_location_src_id.id,
                        'location_dest_id': picking_checker2.default_location_dest_id.id,
                        'etsi_teams_member_no': picking.etsi_teams_member_no,
                        'etsi_teams_member_name': picking.etsi_teams_member_name.id,
                        'etsi_teams_id':  picking.etsi_teams_id.id,
                        'etsi_teams_line_ids':  team_new_list,
                        'state' : 'draft',
                        'teller' : 'damage'
                    })
                
                # Additional, Add serials of damaged into pullouts
                stock_damaged_db = self.env['etsi.pull_out.inventory']
                
                for dmg in team_return_damaged:
                    team = self.env['team.configuration'].search([('team_number','=',dmg['teams_from_damage'])]) 
                    active_name = self.env['stock.picking'].search([('id','=',dmg['active_name'])]) 
                    
                    for item in team:
                        for name in active_name:
                            create_damaged_function = stock_damaged_db.create({
                                'etsi_product_name' : dmg['name'],
                                'etsi_serial': dmg['etsi_serials_field'],
                                'etsi_mac': dmg['etsi_mac_field'],
                                'etsi_smart_card': dmg['etsi_smart_card_field'],
                                'etsi_teams_id' : item.team_number,
                                'transaction_number' : name.name,
                                'etsi_status': 'received',
                                'etsi_receive_date_in': fields.Date.today(),
                                'is_damaged' : True,
                                'description' :dmg['dmg_type']
                            })
                    
                # Execute the damaged function
                return_damaged_function.action_assign()
                return_damaged_function.do_transfer()

                # Update the status of created record for damaged items in stock.picking 
                search_picking = self.env['stock.move'].search([])

                for serial in search_picking:
                    for list_serial in team_return_damaged:
                        search_picking_id = self.env['stock.move'].search([('etsi_serials_field','=',list_serial['etsi_serials_field'])])

                        if search_picking_id:
                            stock_picking = self.env['stock.picking'].search([('id','=', serial.picking_id.id)])
                
                # Update quanity of serials from subscriber issuance
                product_lists_damaged = []
                product_serials_damaged = []

                for plines in rec.damage_list_ids:
                    if picking.etsi_teams_id.id == plines.teams.id:
                        product_lists_damaged.append(plines.product_id)
                        product_serials_damaged.append(plines.etsi_serial_product)

                # For damaged products - Code for updating status 
                if product_lists_damaged and product_serials_damaged:
                    for issued_ids in issued_stats:
                        if issued_ids.etsi_serials_field in product_serials_damaged:
                            issued_ids.update({'issued_field': 'Damaged'})
            
                            for searched_ids in inventory_stats:
                                if searched_ids.etsi_product_id in product_lists_damaged:
                                    if searched_ids.etsi_serial in product_serials_damaged:
                                        searched_ids.update({'etsi_status': 'damaged'})

                                        # update history
                                        searched_ids.write({'etsi_history_lines': [(0,0, {'etsi_operation':'Damaged Location','etsi_transaction_num':picking.id,'etsi_action_date': datetime.today(),'etsi_status':'Damaged','etsi_employee':self.env.user.id,'etsi_teams':picking.etsi_teams_id.id,'etsi_history_quantity': 1,'etsi_transaction_description':'Team to Damage Location'})]})
                        
            # Transfer Items
            if team_return_transfer or team_return or team_return_damaged: # Transfer list or Team Return list
                transfer_picking = self.env['etsi.inventory'].search([])
                inventing = self.env['stock.picking'].search([('picking_type_id.name','=', 'Team Issuance'),('state','not in',['cancel','draft'])])
                trans_ako = self.env['stock.transfer.team.return'].search([])
                
                listahan_ng_trans = []
                final_info = []
                serial_only = []
                store_me_daddy = []
                store_me_mommy = []
                
                serial_stored_nl = []
                serial_stored_move = []
                serial_stored_tmp = []
                
                counter = 0
                final_trans = []
                
                # If reciever is early
                if team_return:
                    for t_hold in rec.return_list_move_holder:
                        # Return List - serial stored
                        if picking.etsi_teams_id.team_number != t_hold.teams.team_number:
                            serial_stored_nl.append(t_hold.etsi_serial_product)
                            serial_only.append(t_hold.etsi_serial_product)
                        
                        # Temporary / Floating database
                        for trans_to2 in trans_ako:
                            if trans_to2: # if database is not empty
                                serial_stored_tmp.append(trans_to2.etsi_serial_product)
                                
                            # Condition / Transaction
                            for nl in serial_stored_nl: # fetch return list  
                                if nl == trans_to2.etsi_serial_product and trans_to2.issued == 'Waiting' and trans_to2.transfer_checker == True and trans_to2.return_checker == False:
                                    # Update existing floating data
                                    trans_to2.update({
                                        'issued': "Done",
                                        "prod_stat": "Done",
                                        'return_checker': True,
                                    })
                                        
                                elif nl in serial_stored_tmp and trans_to2.return_checker == True and trans_to2.transfer_checker == False:
                                    raise UserError("This serial is already returned, Please wait the other team for transfer slip (confirmation)!")
                                
                        # create record if condition above are false
                        if picking.etsi_teams_id.team_number != t_hold.teams.team_number: # filter transfered items only
                            if not trans_ako or t_hold.etsi_serial_product not in serial_stored_tmp: 
                                transfer_picking = self.env['etsi.inventory'].search([('etsi_serial','=', t_hold.etsi_serial_product)])
                                issued_stats = self.env['stock.move'].search([('etsi_serials_field','=', t_hold.etsi_serial_product),('issued_field','=','Deployed')])

                                transfer_picking.update({'etsi_status': 'pending'}) # update product status in etsi_inventory -> Pending transfer
                                # update history
                                transfer_picking.write({'etsi_history_lines': [(0,0, {'etsi_operation':'Transfer (Normal Return)','etsi_transaction_num':picking.id,'etsi_action_date': datetime.today(),'etsi_status':'Pending Transfer','etsi_employee':self.env.user.id,'etsi_teams':picking.etsi_teams_id.id,'etsi_history_quantity': 1,'etsi_transaction_description':'Team Location to Warehouse'})]})
                                issued_stats.update({'issued_field': 'Available'}) # update product status in move -> Available

                                # Create data function for transfer items
                                return_transfer_function = self.env['stock.transfer.team.return'].create({
                                    'product_id': t_hold.product_id.id,
                                    'quantity': 1.0,
                                    'issued': "Waiting",
                                    'prod_stat': "Pending",
                                    'etsi_serial_product': t_hold.etsi_serial_product,
                                    'etsi_mac_product':  t_hold.etsi_mac_product,
                                    'etsi_smart_card':  t_hold.etsi_smart_card,
                                    'team_num_from': t_hold.teams.id,
                                    'team_num_to': picking.etsi_teams_id.id,
                                    'transfer_checker': False,
                                    'return_checker': True,
                                })

                # Damage transfer - if team returned has damaged product in transfer transact
                if team_return_damaged:
                    transfer_picking = self.env['etsi.inventory'].search([])
                    trans_ako = self.env['stock.transfer.team.return'].search([])

                    sira_list = []
                    sirang_trans = []

                    for sira in rec.damage_list_ids: # fetch damaged serials
                        for trans in trans_ako: # fetch temp data
                            sirang_trans.append(trans.etsi_serial_product) # fetch serials for validations
                            serial_only.append(trans.etsi_serial_product)

                            if sira.etsi_serial_product == trans.etsi_serial_product and trans.issued == 'Waiting' and trans.transfer_checker and trans.return_checker == False and trans.damaged == False:
                                # Update existing floatong data
                                trans.update({
                                    'issued': "Done",
                                    'prod_stat': "Done",
                                    'return_checker': True,
                                    'damaged': True
                                })
                            elif sira.etsi_serial_product == trans.etsi_serial_product and trans.return_checker and trans.damaged and trans.transfer_checker == False:
                                raise UserError("This serial is already returned as damaged, Please wait the other team for transfer slip (confirmation)!")
                        
                        # create record if condition above are false
                        if picking.etsi_teams_id.team_number != sira.teams.team_number: # filter transfered items only
                            if not trans_ako or sira.etsi_serial_product not in sirang_trans: 
                                transfer_picking = self.env['etsi.inventory'].search([('etsi_serial','=', sira.etsi_serial_product)])
                                issued_stats = self.env['stock.move'].search([('etsi_serials_field','=', sira.etsi_serial_product),('issued_field','=','Deployed')])
                                
                                transfer_picking.update({'etsi_status': 'pending'}) # update product status in etsi_inventory -> Pending transfer
                                # update history
                                transfer_picking.write({'etsi_history_lines': [(0,0, {'etsi_operation':'Transfer (Damage Location)','etsi_transaction_num':picking.id,'etsi_action_date': datetime.today(),'etsi_status':'Pending Transfer','etsi_employee':self.env.user.id,'etsi_teams':picking.etsi_teams_id.id,'etsi_history_quantity': 1,'etsi_transaction_description':'Team to Damage Location'})]})

                                # Create data function for transfer items
                                return_transfer_function = self.env['stock.transfer.team.return'].create({
                                    'product_id': sira.product_id.id,
                                    'quantity': 1.0,
                                    'issued': "Waiting",
                                    'prod_stat': "Pending",
                                    'etsi_serial_product': sira.etsi_serial_product,
                                    'etsi_mac_product':  sira.etsi_mac_product,
                                    'etsi_smart_card':  sira.etsi_smart_card,
                                    'team_num_from': sira.teams.id,
                                    'team_num_to': picking.etsi_teams_id.id,
                                    'transfer_checker': False,
                                    'return_checker': True,
                                    'damaged': True
                                })

                # who transfered the item
                if team_return_transfer:
                    for t_hold in rec.transfer_list_ids:
                        # Transfer info
                        listahan_ng_trans.append({
                            'product_id': t_hold.product_id.id,
                            'serial': t_hold.etsi_serial_product,
                            'mac': t_hold.etsi_mac_product,
                            'smart_card': t_hold.etsi_smart_card,
                            'source': t_hold.active_ako.id,
                            'team_from': t_hold.teams_from.id,
                            'team_to': t_hold.teams_to.id,
                            'team_to_name': t_hold.teams_to.team_number,
                            'two_team': t_hold.if_two_team
                        })
                        # Serial only
                        serial_only.append(t_hold.etsi_serial_product)
                    
                    for trans_to in listahan_ng_trans:
                        for trans_to2 in trans_ako:
                            if trans_to2: # get true data
                                serial_stored_tmp.append(trans_to2.etsi_serial_product) # store serial for validation
                                
                                if trans_to['serial'] in serial_stored_tmp and trans_to2.issued == 'Waiting' and trans_to2.return_checker == True:
                                    for pick in inventing:
                                        if pick.etsi_teams_id.id == trans_to['team_to']:
                                            store_me_daddy.append(pick.id)
                                    
                                    trans_to2.update({
                                        'issued': "Done",
                                        'prod_stat': "Done",
                                        'transfer_checker': True,
                                        'source': max(store_me_daddy)
                                    })
                                    
                                elif trans_to2.return_checker == False and trans_to2.transfer_checker == True and trans_to['serial'] == trans_to2.etsi_serial_product:
                                    raise ValidationError("This serial is already transfered, Please wait the other team for updates!")
                                    
                        # if database is empty / serial does not exist in temp data
                        if not trans_ako or trans_to['serial'] not in serial_stored_tmp:
                            transfer_picking = self.env['etsi.inventory'].search([('etsi_serial','=', trans_to['serial'])])

                            if trans_to['two_team']: # if its true
                                trans_move = self.env['stock.move'].search([('etsi_serials_field', '=', trans_to['serial']), ('issued_field','=','Deployed')])
                                for pick in inventing: # fetch stock picking
                                    if pick.etsi_teams_id.id == trans_to['team_to']: # filter data depends on teams_to
                                        store_me_daddy.append(pick.id)

                                if store_me_daddy: # check if list has value      
                                    for move in trans_move: # update stock.move
                                        if move.etsi_serials_field: # get true data 
                                            move.update({'picking_id': max(store_me_daddy)}) # Replace team_issuance ref number
                                    # update history - etsi inventory
                                    transfer_picking.write({'etsi_history_lines': [(0,0, {'etsi_operation':'Transfer Item','etsi_transaction_num':picking.id,'etsi_action_date': datetime.today(),'etsi_status':'Deployed','etsi_employee':self.env.user.id,'etsi_teams':trans_to['team_to'],'etsi_history_quantity': 1,'etsi_transaction_description':'Team to another Team Location'})]})
                                    transfer_picking.update({'etsi_team_in': trans_to['team_to']}) # update teams

                                    # Create data function for transfer items
                                    return_transfer_function = self.env['stock.transfer.team.return'].create({
                                        'product_id': trans_to['product_id'],
                                        'quantity': 1.0,
                                        'issued': "Done",
                                        'prod_stat': "Done",
                                        'etsi_serial_product': trans_to['serial'],
                                        'etsi_mac_product':  trans_to['mac'],
                                        'etsi_smart_card':  trans_to['smart_card'],
                                        # 'source': max(store_me_mommy),
                                        'team_num_from': trans_to['team_from'],
                                        'team_num_to': trans_to['team_to'],
                                        'transfer_checker': True,
                                        'return_checker': True,
                                        'two_man': True
                                    })
                                    
                                else: # if no value - no issued products
                                    check = "The team '{}' you entered has no issued products yet.".format(trans_to['team_to_name'])
                                    raise UserError(check)
                                
                            else: # if team-to is 1 man team
                                for pick in inventing: # fetch stock picking
                                    if pick.etsi_teams_id.id == trans_to['team_to']: # filter data depends on teams_to
                                        store_me_mommy.append(pick.id)
                                
                                # update product status -> pending transfer
                                transfer_picking.update({'etsi_status': 'pending'}) 
                                # update history
                                transfer_picking.write({'etsi_history_lines': [(0,0, {'etsi_operation':'Transfer Item','etsi_transaction_num':picking.id,'etsi_action_date': datetime.today(),'etsi_status':'Pending Transfer','etsi_employee':self.env.user.id,'etsi_teams':picking.etsi_teams_id.id,'etsi_history_quantity': 1,'etsi_transaction_description':'Team to another Team Location'})]})

                                if store_me_mommy: # check if list has value        
                                    # Create data function for transfer items
                                    return_transfer_function = self.env['stock.transfer.team.return'].create({
                                        'product_id': trans_to['product_id'],
                                        'quantity': 1.0,
                                        'issued': "Waiting",
                                        'prod_stat': "Pending",
                                        'etsi_serial_product': trans_to['serial'],
                                        'etsi_mac_product':  trans_to['mac'],
                                        'etsi_smart_card':  trans_to['smart_card'],
                                        'source': max(store_me_mommy),
                                        'team_num_from': trans_to['team_from'],
                                        'team_num_to': trans_to['team_to'],
                                        'transfer_checker': True,
                                        'return_checker': False,
                                    })
                                else: # if no value - no issued products
                                    check = "The team '{}' you entered has no issued products yet.".format(trans_to['team_to_name'])
                                    raise UserError(check)

                # If transfer transaction is finished / confirmed update product location
                for list_trans in trans_ako:
                    # Check if the floating data is ready - to update the product list on team issuance (Product reciever)
                    if list_trans.etsi_serial_product in serial_only and list_trans.issued == "Done" and list_trans.return_checker == True and list_trans.transfer_checker == True and list_trans.two_man == False:
                        final_info.append({
                            'serial': list_trans.etsi_serial_product,
                            'source': list_trans.source.id,
                            'team_to': list_trans.team_num_to.id,
                            'installed': list_trans.installed,
                            'damaged': list_trans.damaged,
                            '2man': list_trans.two_man
                        })
                
                # Update record of product recipient's team issuance
                for fin in final_info:
                    trans_move = self.env['stock.move'].search([('etsi_serials_field', '=', fin['serial']), ('issued_field','=','Deployed')])
                    
                    for move in trans_move: # update stock.move
                        if move.etsi_serials_field: # get true data
                            if fin['installed'] == True: # if item is installed
                                move.update({'picking_id': fin['source']}) # Replace team_issuance ref number
                                move.update({'issued_field': 'Used'}) # Update product status - to Used
                            elif fin['damaged'] == True: # if transfered item is damage
                                move.update({'picking_id': fin['source']}) # Replace team_issuance ref number
                                move.update({'issued_field': 'Damaged'}) # Update product status - to Damaged
                            else: # if not installed
                                move.update({'picking_id': fin['source']}) # Replace team_issuance ref number
                                move.update({'issued_field': 'Available'}) # Update product status - to Available

                    for inventory in transfer_picking: # update etsi.inventory - team number
                        if inventory.etsi_serial == fin['serial']:
                            if fin['installed'] == True: # if item is installed
                                inventory.update({'etsi_status': 'used'}) # update product status
                                inventory.update({'etsi_team_in': fin['team_to']}) # update team number
                                inventory.update({'etsi_date_issued_in': datetime.today()}) # update date issued       
                                # update history                        
                                inventory.write({'etsi_history_lines': [(0,0, {'etsi_operation':'Transfer (Subscriber Issuance)','etsi_transaction_num':picking.id,'etsi_action_date': datetime.today(),'etsi_status':'Used','etsi_employee':self.env.user.id,'etsi_teams':fin['team_to'],'etsi_history_quantity': 1,'etsi_transaction_description':'Team to Partner Location'})]})
                            elif fin['damaged'] == True: # if transfered item is damage
                                inventory.update({'etsi_status': 'damaged'}) # update product status
                                # update history                        
                                inventory.write({'etsi_history_lines': [(0,0, {'etsi_operation':'Transfer (Damaged Location)','etsi_transaction_num':picking.id,'etsi_action_date': datetime.today(),'etsi_status':'Damaged','etsi_employee':self.env.user.id,'etsi_teams':fin['team_to'],'etsi_history_quantity': 1,'etsi_transaction_description':'Team to Damage Location'})]})
                            else: # if not installed
                                inventory.update({'etsi_status': 'available'}) # update product status -> available
                                inventory.update({'etsi_date_returned_in': datetime.today()}) # update date returned
                                inventory.update({'etsi_team_in': False}) 
                                # update history
                                inventory.write({'etsi_history_lines': [(0,0, {'etsi_operation':'Transfer (Normal Return)','etsi_transaction_num':picking.id,'etsi_action_date': datetime.today(),'etsi_status':'Available','etsi_employee':self.env.user.id,'etsi_teams':fin['team_to'],'etsi_history_quantity': 1,'etsi_transaction_description':'Team Location to Warehouse'})]})
                
        # if all transation is done update current form in done state
        stock_picking_db = self.env['stock.picking'].search([('name','=', picking.name)])
        if team_return : # If user have return list, finis the transaction
            stock_picking_db.do_transfer()
        else: # If not, finish the form 
            stock_picking_db.update({'state': 'done'})

    @api.model
    def default_get(self, fields):
        res = super(Return_list_holder, self).default_get(fields)
        picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))

        # if form is in done state, raise a validation
        if picking.state == 'done':
            raise ValidationError("This form is no longer available to return. (Only in draft state)")
        
        # Declare return value in teller
        if picking.picking_type_id.name == "Team Return":
            picking.teller = "return"
        
        return_list_move = []
        damage_list_move = []
        transfer_list_move = []
        for p in picking:
            for move in p.return_list:
                trans = self.env['stock.transfer.team.return'].search([('etsi_serial_product','=', move.etsi_serial_product)]) # fetch temp transfer data
                
                if move.transfer_checker:
                    if move.teams_from.id != picking.etsi_teams_id.id: # check if teams from is not the same on team return
                        raise UserError("Returned Team and 'Teams From' must be the same!")
                    if move.teams_from.id == move.teams_to.id: # check if teams_from and teams_to is the same
                        raise UserError("'Teams from' and 'Teams to' cannot be the same.")
                    if trans: # check if trans has value
                        if move.teams_to.id != trans.team_num_to.id and trans.team_num_to.id != False: # check if teams_to and team_num_to are'nt the same
                            raise UserError("The 'Teams to' are not the same as the team that returned the item.")
                if move.damage_checker and trans and picking.etsi_teams_id.id != trans.team_num_to.id or move.return_checker and trans and picking.etsi_teams_id.id != trans.team_num_to.id:
                    raise UserError("This serial number {} is available in the transfer list. Please check the transfer checkbox to confirm!".format(move.etsi_serial_product))
                    
                if picking.return_list:
                    # If CATV is selected
                    if move.etsi_smart_card:
                        if move.return_checker:
                            return_list_move.append((
                                0, 0, {
                                'product_id': move.product_id.id, 
                                'quantity': move.quantity, 
                                # 'move_id': move.id, 
                                'product_uom' : move.product_uom.id,
                                'issued': 'Available',
                                'etsi_serial_product': move.etsi_serial_product, 
                                'etsi_smart_card': move.etsi_smart_card,
                                'active_ako' : move.active_ako.id,
                                'active_name' : p.id,
                                'teams': move.teams.id
                            }))
                        if move.damage_checker:
                            damage_list_move.append((
                                0, 0, {
                                'product_id': move.product_id.id, 
                                'quantity': move.quantity, 
                                'product_uom' : move.product_uom.id,
                                'issued': 'Damaged',
                                'dmg_type': move.dmg_type,
                                'etsi_serial_product': move.etsi_serial_product, 
                                'etsi_smart_card': move.etsi_smart_card,
                                'active_ako' : move.active_ako.id,
                                'active_name' : p.id,

                                # for pullouts
                                'teams_from_damage' : move.teams_from_damage,
                                'active_name' : picking.id,

                                # For transfer damage
                                'teams': move.teams.id
                                
                            }))
                        if move.transfer_checker:
                            transfer_list_move.append((
                                0, 0, {
                                'product_id': move.product_id.id, 
                                'quantity': move.quantity, 
                                # 'move_id': move.id, 
                                'product_uom' : move.product_uom.id,
                                'issued': move.issued,
                                'etsi_serial_product': move.etsi_serial_product, 
                                'etsi_smart_card': move.etsi_smart_card,
                                'teams_from': move.teams_from.id,
                                'teams_to': move.teams_to.id,
                                'active_ako' : move.active_ako.id,
                                'active_name' : p.id,
                                'if_two_team': move.if_two_team
                            }))
                    # If MODEM is selected
                    if move.etsi_mac_product:
                        if move.return_checker:
                            return_list_move.append((
                                0, 0, {
                                'product_id': move.product_id.id, 
                                'quantity': move.quantity, 
                                # 'move_id': move.id, 
                                'product_uom' : move.product_uom.id,
                                'issued': 'Available',
                                'etsi_serial_product': move.etsi_serial_product, 
                                'etsi_mac_product': move.etsi_mac_product,
                                'etsi_smart_card': move.etsi_smart_card,
                                'active_ako' : move.active_ako.id,
                                'active_name' : p.id,
                                'teams': move.teams.id
                            }))
                        if move.damage_checker:
                            damage_list_move.append((
                                0, 0, {
                                'product_id': move.product_id.id, 
                                'quantity': move.quantity, 
                                # 'move_id': move.id, 
                                'product_uom' : move.product_uom.id,
                                'issued': 'Damaged',
                                'dmg_type': move.dmg_type,
                                'etsi_serial_product': move.etsi_serial_product, 
                                'etsi_mac_field': move.etsi_mac_product,
                                'etsi_smart_card': move.etsi_smart_card,
                                'active_ako' : move.active_ako.id,
                                'active_name' : p.id,

                                # for pullouts
                                'teams_from_damage' : move.teams_from_damage,
                                'active_name' : picking.id,

                                # For transfer damage
                                'teams': move.teams.id
                            }))
                        if move.transfer_checker:
                            transfer_list_move.append((
                                0, 0, {
                                'product_id': move.product_id.id, 
                                'quantity': move.quantity, 
                                # 'move_id': move.id, 
                                'product_uom' : move.product_uom.id,
                                'issued': move.issued,
                                'etsi_serial_product': move.etsi_serial_product, 
                                'etsi_mac_product': move.etsi_mac_product,
                                'etsi_smart_card': move.etsi_smart_card,
                                'teams_from': move.teams_from.id,
                                'teams_to': move.teams_to.id,
                                'active_ako' : move.active_ako.id,
                                'active_name' : p.id,
                                'if_two_team': move.if_two_team
                            }))
                    # If item has no MAC ID and Smart Card
                    if not move.etsi_smart_card and not move.etsi_mac_product:
                        if move.return_checker:
                            return_list_move.append((
                                0, 0, {
                                'product_id': move.product_id.id, 
                                'quantity': move.quantity, 
                                # 'move_id': move.id, 
                                'product_uom' : move.product_uom.id,
                                'issued': 'Available',
                                'etsi_serial_product': move.etsi_serial_product, 
                                'active_ako' : move.active_ako.id,
                                'active_name' : p.id,
                                'teams': move.teams.id
                            }))
                        if move.damage_checker:
                            damage_list_move.append((
                                0, 0, {
                                'product_id': move.product_id.id, 
                                'quantity': move.quantity, 
                                # 'move_id': move.id, 
                                'product_uom' : move.product_uom.id,
                                'issued': 'Damaged',
                                'dmg_type': move.dmg_type,
                                'etsi_serial_product': move.etsi_serial_product, 
                                'active_ako' : move.active_ako.id,
                                'active_name' : p.id,

                                # for pullouts
                                'teams_from_damage' : move.teams_from_damage,
                                'active_name' : picking.id,

                                # For transfer damage
                                'teams': move.teams.id
                            }))
                        if move.transfer_checker:
                            transfer_list_move.append((
                                0, 0, {
                                'product_id': move.product_id.id, 
                                'quantity': move.quantity, 
                                # 'move_id': move.id, 
                                'product_uom' : move.product_uom.id,
                                'issued': move.issued,
                                'etsi_serial_product': move.etsi_serial_product, 
                                'teams_from': move.teams_from.id,
                                'teams_to': move.teams_to.id,
                                'active_ako' : move.active_ako.id,
                                'active_name' : p.id,
                                'if_two_team': move.if_two_team
                            }))
        
        if not return_list_move and not damage_list_move and not transfer_list_move:
            raise UserError(_("No products to return (only in team return operational type / please select transaction type to continue)!"))
        if 'return_list_move_holder' in fields or 'damage_list_ids' in fields or 'transfer_list_ids' in fields:
                # Return
                res.update({'return_list_move_holder': return_list_move})
                # Damage
                res.update({'damage_list_ids': damage_list_move})
                # Transfer
                res.update({'transfer_list_ids': transfer_list_move})
        if 'etsi_teams_id' in fields:
            res.update({'etsi_teams_id': picking.etsi_teams_id.id})
        return res

class TransferLists(models.Model):
    _name = "stock.transfer.team.return"
    
    product_id =  fields.Many2one('product.product') 
    quantity = fields.Float('Quantity')
    issued = fields.Char(string="Product Status")
    prod_stat = fields.Char(string="Product Status")
    etsi_serial_product = fields.Char(string="Serial ID")
    etsi_mac_product = fields.Char(string="MAC ID")
    etsi_smart_card = fields.Char(string="Smart Card")
    transfer_checker = fields.Boolean("Transfered")
    return_checker = fields.Boolean("Returned")
    source = fields.Many2one('stock.picking')
    team_num_from = fields.Many2one('team.configuration', string="From Team")
    team_num_to = fields.Many2one('team.configuration', string="To Team")
    date_transfered = fields.Date(default=datetime.today(), string="Date of Transaction")
    installed = fields.Boolean('Installed')
    damaged = fields.Boolean('Damaged')
    two_man = fields.Boolean('XFRD')

    @api.multi
    def delete(self):
        for rec in self:
            if rec.prod_stat == "Pending":
                raise UserError("This record cannot be deleted because the product status is 'Pending'!")
            elif rec.prod_stat == "Done":
                self.unlink()
        # return super(TransferLists, self).unlink()
        # Return button in true value.
        return True

class Return_list_childs(models.Model):
    _name = 'stock.picking.return.list'

    # Connects to return_list
    return_list_connector = fields.Many2one('stock.picking')
    # # Connects to return_list_moves
    # return_list_moves_connector = fields.Many2one('stock.picking.return.list.holder')

    product_id =  fields.Many2one('product.product') 
    quantity = fields.Float('Quantity',default=1.0)
    issued = fields.Char(string="Product Status")
    etsi_serial_product = fields.Char(string="Serial ID")
    etsi_mac_product = fields.Char(string="MAC ID")
    etsi_smart_card = fields.Char(string="Smart Card")
    active_ako = fields.Many2one('stock.picking')
    product_uom = fields.Many2one('product.uom', 'Unit of Measure')
    product_uom_qty = fields.Float('Quantity',default=1.0)
    active_name = fields.Char('Active Name')
    
    transfer_checker = fields.Boolean("Transfer")
    damage_checker = fields.Boolean("Damage")
    dmg_type = fields.Selection([
        ('physical','Physical Damage'),
        ('boot','Not Bootable'),
        ('power','No Power')
    ], string="Damage Type")
    return_checker = fields.Boolean("Return")
    teams = fields.Many2one('team.configuration')
    teams_from = fields.Many2one('team.configuration', string="Teams From")
    teams_to = fields.Many2one('team.configuration', string="Teams To")
    if_two_team = fields.Boolean("XFRD", default=False)
    
    teams_from_duplicate = fields.Many2one('team.configuration', related='teams_from')
    teams_to_duplicate = fields.Many2one('team.configuration')
    product_id_duplicate =  fields.Many2one('product.product', related="product_id") 
    product_uom_duplicate = fields.Many2one('product.uom', related="product_uom")
    issued_duplicate = fields.Char(related="issued")
    if_two_team_duplicate = fields.Boolean(related="if_two_team")
    # For Pull-outs
    teams_from_damage = fields.Char()
    
    @api.multi 
    @api.onchange('etsi_serial_product','etsi_mac_product','etsi_smart_card', 'return_checker', 'damage_checker','transfer_checker','teams_to')
    def onchange_transfer(self):
        for rec in self:
            etsi_inv = self.env['etsi.inventory'].search([])
            
            # Auto Fill Function
            # search available products - stock.move model
            pm_search_sr = self.env['stock.move'].search([('etsi_serials_field','=', rec.etsi_serial_product), ('issued_field','=','Deployed')])
            pm_search_mc = self.env['stock.move'].search([('etsi_mac_field','=', rec.etsi_mac_product), ('issued_field','=','Deployed')])
            pm_search_sc = self.env['stock.move'].search([('etsi_smart_card_field','=', rec.etsi_smart_card), ('issued_field','=','Deployed')])
            
            ei_search_sr = self.env['etsi.inventory'].search([('etsi_serial','=', rec.etsi_serial_product)])
            ei_search_mc = self.env['etsi.inventory'].search([('etsi_mac','=', rec.etsi_mac_product)])
            ei_search_sc = self.env['etsi.inventory'].search([('etsi_smart_card','=', rec.etsi_smart_card)])
            
            search_name = self.env['stock.picking'].search([('name','=', rec.active_ako.name)])
            
            transfer_list = self.env['stock.transfer.team.return'].search([('etsi_serial_product','=', rec.etsi_serial_product)])
            
            list_ako = []
            para_sa_trans_sr = []
            para_sa_trans_stat = []
            
            # Valued data only passes
            if rec.etsi_serial_product != False or rec.etsi_mac_product != False or rec.etsi_smart_card != False:
                # Check if data inputted is available
                # MAC ID
                if rec.etsi_mac_product:
                    # # Validation for issued status
                    if pm_search_mc:
                        for mac in pm_search_mc:
                            for mac2 in ei_search_mc:
                                if mac.issued_field == "Deployed":
                                    # Auto fill statements
                                    rec.product_id = mac.product_id.id
                                    rec.etsi_serial_product = mac.etsi_serials_field
                                    rec.etsi_smart_card = mac.etsi_smart_card_field
                                    rec.issued = "Deployed"
                                    rec.active_ako = mac.picking_id.id
                                    rec.quantity = 1.00
                                    rec.product_uom = 1
                                    rec.teams = mac2.etsi_team_in.id
                                else:
                                    raise ValidationError("This Product is not Deployed / Already installed (Used)")
                    else:
                        # Check if item is available in transfer list / pending transfer
                        for mac2 in ei_search_mc:
                            transfer_mc = self.env['stock.transfer.team.return'].search([('etsi_smart_card','=', rec.etsi_mac_product)])
                            if transfer_mc:
                                # Auto fill statements
                                rec.product_id = mac2.etsi_product_id.id
                                rec.etsi_serial_product = mac2.etsi_serial
                                rec.etsi_smart_card = mac2.etsi_smart_card
                                rec.issued = "Deployed"
                                rec.quantity = 1.00
                                rec.product_uom = 1
                                rec.teams = mac2.etsi_team_in.id
                            else:
                                raise ValidationError("This Product is not Deployed / Already installed (Used)")
                
                # Smart Card
                if rec.etsi_smart_card:
                    # Validation for issued status
                    if pm_search_sc:
                        for scard in pm_search_sc:
                            for scard2 in ei_search_sc:
                                if scard.issued_field == "Deployed":
                                    # Auto fill statements
                                    rec.product_id = scard.product_id.id
                                    rec.etsi_mac_product = scard.etsi_mac_field
                                    rec.etsi_serial_product = scard.etsi_serials_field
                                    rec.issued = "Deployed"
                                    rec.active_ako = scard.picking_id.id
                                    rec.quantity = 1.00
                                    rec.product_uom = 1
                                    rec.teams = scard2.etsi_team_in.id
                                else:
                                    raise ValidationError("This Product is not Deployed / Already installed (Used)")
                    else:
                        # Check if item is available in transfer list / pending transfer
                        for scard2 in ei_search_sc:
                            transfer_sc = self.env['stock.transfer.team.return'].search([('etsi_smart_card','=', rec.etsi_smart_card)])
                            if transfer_sc:
                                # Auto fill statements
                                rec.product_id = scard2.etsi_product_id.id
                                rec.etsi_mac_product = scard2.etsi_mac
                                rec.etsi_serial_product = scard2.etsi_serial
                                rec.issued = "Deployed"
                                rec.quantity = 1.00
                                rec.product_uom = 1
                                rec.teams = scard2.etsi_team_in.id
                            else:
                                raise ValidationError("This Product is not Deployed / Already installed (Used)")
                        
                # Serial Number
                if rec.etsi_serial_product:
                    if pm_search_sr: # Validation for issued status
                        for ser in pm_search_sr: # check stock.move
                            for ser2 in ei_search_sr: # check etsi.inventory
                                if transfer_list: # check if transfer list is true
                                    # check stock.transfer.team.return
                                    for t_list in transfer_list:
                                        para_sa_trans_sr.append(t_list.etsi_serial_product)
                                        para_sa_trans_stat.append(t_list.issued)
                                        
                                    # check stock.transfer.team.return
                                    if ser2.etsi_status == "deployed":
                                        # Auto fill statements
                                        rec.product_id = ser.product_id.id
                                        rec.etsi_mac_product = ser.etsi_mac_field
                                        rec.etsi_smart_card = ser.etsi_smart_card_field
                                        rec.issued = "Deployed"
                                        rec.active_ako = ser.picking_id.id
                                        rec.quantity = 1.00
                                        rec.product_uom = 1
                                        # rec.teams_from = s_name.etsi_teams_id.id
                                        rec.teams = ser2.etsi_team_in.id
                                        rec.teams_from_damage = ser2.etsi_team_in.team_number
                                    else:
                                        for t_stat in para_sa_trans_stat:
                                            if t_stat == "Waiting":
                                                # Auto fill statements
                                                rec.product_id = ser.product_id.id
                                                rec.etsi_mac_product = ser.etsi_mac_field
                                                rec.etsi_smart_card = ser.etsi_smart_card_field
                                                rec.issued = "Deployed"
                                                rec.active_ako = ser.picking_id.id
                                                rec.quantity = 1.00
                                                rec.product_uom = 1
                                                rec.teams = ser2.etsi_team_in.id
                                            elif t_stat == "Done":
                                                raise ValidationError("This Product is already transfered!")
                                            else:
                                                raise ValidationError("This Product is not Deployed / Already installed (Used)")
                                else:
                                    # check stock.transfer.team.return
                                    if ser2.etsi_status == "deployed":
                                        # Auto fill statements
                                        rec.product_id = ser.product_id.id
                                        rec.etsi_mac_product = ser.etsi_mac_field
                                        rec.etsi_smart_card = ser.etsi_smart_card_field
                                        rec.issued = "Deployed"
                                        rec.active_ako = ser.picking_id.id
                                        rec.quantity = 1.00
                                        rec.product_uom = 1
                                        rec.teams = ser2.etsi_team_in.id
                                        rec.teams_from_damage = ser2.etsi_team_in.team_number
                                    else:
                                        raise ValidationError("This Product is not Deployed / Already installed (Used)")
                    else:
                        # Check if item is available in transfer list / pending transfer
                        for ser2 in ei_search_sr: # check etsi.inventory
                            if transfer_list: # check if transfer list is true
                                if ser2.etsi_status == "pending":
                                    # Auto fill statements
                                    rec.product_id = ser2.etsi_product_id.id
                                    rec.etsi_mac_product = ser2.etsi_mac
                                    rec.etsi_smart_card = ser2.etsi_smart_card
                                    rec.issued = "Available"
                                    rec.quantity = 1.00
                                    rec.product_uom = 1
                                    rec.teams = ser2.etsi_team_in.id
                                    rec.teams_from_damage = ser2.etsi_team_in.team_number
                                else:
                                    raise ValidationError("This Product is not Deployed / Already installed (Used)")
                                
                    # Validation for checkerssss
                    team_conf = self.env['team.configuration'].search([('team_number','=', rec.teams_to.team_number)])
                    # Return
                    if rec.return_checker:
                        rec.damage_checker = False
                        rec.transfer_checker = False
                        rec.teams_from = False
                        rec.teams_to = False
                        rec.dmg_type = False
                    # Damage
                    elif rec.damage_checker:
                        rec.return_checker = False
                        rec.transfer_checker = False
                        rec.teams_from = False
                        rec.teams_to = False
                    # Transfer
                    elif rec.transfer_checker:        
                        # Auto-fill teams_from
                        search_name = self.env['stock.transfer.team.return'].search([('etsi_serial_product','=', rec.etsi_serial_product)])
                        search_name2 = self.env['etsi.inventory'].search([('etsi_serial','=', rec.etsi_serial_product)])
                        
                        if search_name: # check if search have value
                            for s_name in search_name:
                                rec.teams_from = s_name.team_num_from.id
                        else: # if have'nt, get team_from value to etsi_inventory
                            for s_name in search_name2:
                                rec.teams_from = s_name.etsi_team_in.id
                            
                        rec.return_checker = False
                        rec.damage_checker = False
                        rec.dmg_type = False
                    
                    # dropdown fields
                    if rec.transfer_checker == False:
                        rec.teams_from = False
                        rec.teams_to = False
                        rec.if_two_team = False
                    if rec.damage_checker == False:
                        rec.dmg_type = False

                    if rec.teams_to: # if team to is true
                        for team_kups in team_conf: # fetch team conf
                            if team_conf.teamType == 'two_man':
                                rec.if_two_team = True
                            else:
                                rec.if_two_team = False

class Return_list_child(models.TransientModel):
    _name = 'stock.picking.return.list_2'

    # # Connects to return_list
    # return_list_connector = fields.Many2one('stock.picking')
    # Connects to return_list_moves
    return_list_moves_connector_2 = fields.Many2one('stock.picking.return.list.holder')

    damage_checker = fields.Boolean('Damaged')
    product_id =  fields.Many2one('product.product') 
    quantity = fields.Float('Quantity')
    issued = fields.Char(string="Product Status")
    etsi_serial_product = fields.Char(string="Serial ID")
    etsi_mac_product = fields.Char(string="MAC ID")
    etsi_smart_card = fields.Char(string="Smart Card")
    active_ako = fields.Many2one('stock.picking')
    active_name = fields.Many2one('stock.picking')
    product_uom = fields.Many2one('product.uom', 'Unit of Measure')
    product_uom_qty = fields.Float('Quantity',default=1.0)
    teams = fields.Many2one('team.configuration')
    # transfer_checker = fields.Boolean("Transfer")
    # teams = fields.Many2one('team.configuration')

class DamageLists(models.TransientModel):
    _name = "stock.picking.damage.list"
    
    # Connects to return_list_moves
    damage_list_id = fields.Many2one('stock.picking.return.list.holder')

    product_id =  fields.Many2one('product.product') 
    quantity = fields.Float('Quantity')
    issued = fields.Char(string="Product Status")
    dmg_type = fields.Selection([
        ('physical','Physical Damage'),
        ('boot','Not Bootable'),
        ('power','No Power')
    ], string="Damage Type")
    etsi_serial_product = fields.Char(string="Serial ID")
    etsi_mac_product = fields.Char(string="MAC ID")
    etsi_smart_card = fields.Char(string="Smart Card")
    active_ako = fields.Many2one('stock.picking')
    active_name = fields.Many2one('stock.picking')
    product_uom = fields.Many2one('product.uom', 'Unit of Measure')
    product_uom_qty = fields.Float('Quantity',default=1.0)
    teams_from_damage = fields.Char()
    teams = fields.Many2one('team.configuration')
    
class TransferLists(models.TransientModel):
    _name = "stock.picking.transfer.list"
    
    # Connects to return_list_moves
    transfer_list_id = fields.Many2one('stock.picking.return.list.holder')

    product_id =  fields.Many2one('product.product') 
    quantity = fields.Float('Quantity')
    issued = fields.Char(string="Product Status")
    etsi_serial_product = fields.Char(string="Serial ID")
    etsi_mac_product = fields.Char(string="MAC ID")
    etsi_smart_card = fields.Char(string="Smart Card")
    active_ako = fields.Many2one('stock.picking')
    active_name = fields.Many2one('stock.picking')
    product_uom = fields.Many2one('product.uom', 'Unit of Measure')
    product_uom_qty = fields.Float('Quantity',default=1.0)
    teams_from = fields.Many2one('team.configuration', string="Teams From")
    teams_to = fields.Many2one('team.configuration', string="Teams To")
    if_two_team = fields.Boolean("XFRD")


# Model for accepting returned items
class ReturnedItems(models.Model):
    _name='stock.picking.returned.item.list'
      # Connects to return_list
    return_item_connector = fields.Many2one('stock.picking')

    product_id =  fields.Many2one('product.product',string='Product') 
    quantity = fields.Float('Quantity')
    issued = fields.Char(string="Product Status")
    etsi_serial_product = fields.Char(string="Serial ID")
    etsi_mac_product = fields.Char(string="MAC ID")
    etsi_smart_card = fields.Char(string="Smart Card")
    active_ako = fields.Many2one('stock.picking')
    active_name = fields.Many2one('stock.picking')
    product_uom = fields.Many2one('product.uom', 'Unit of Measure')
    product_uom_qty = fields.Float('Quantity',default=1.0)
    teams = fields.Many2one('team.configuration')

# Model for accepting damaged items

class DamagedItems(models.Model):
    _name = 'stock.picking.damaged.item.list'

    damaged_item_connector = fields.Many2one('stock.picking')

    product_id =  fields.Many2one('product.product',string='Product') 
    quantity = fields.Float('Quantity')
    issued = fields.Char(string="Product Status")
    etsi_serial_product = fields.Char(string="Serial ID")
    etsi_mac_product = fields.Char(string="MAC ID")
    etsi_smart_card = fields.Char(string="Smart Card")
    active_ako = fields.Many2one('stock.picking')
    active_name = fields.Many2one('stock.picking')
    product_uom = fields.Many2one('product.uom', 'Unit of Measure')
    product_uom_qty = fields.Float('Quantity',default=1.0)
    teams = fields.Many2one('team.configuration')
    dmg_type = fields.Selection([
        ('physical','Physical Damage'),
        ('boot','Not Bootable'),
        ('power','No Power')
    ], string="Damage Type")
    
    teams_from_damage = fields.Char()


class ValidationProcess(models.TransientModel):
    _inherit ='stock.immediate.transfer'
        # bypass mark as to do since it was remove
    @api.multi
    def process(self):
        self.ensure_one()
        # If still in draft => confirm and assign
        if self.pick_id.state == 'draft'  :
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