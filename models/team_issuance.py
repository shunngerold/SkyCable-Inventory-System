from odoo import api, fields, models, _
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from odoo.exceptions import ValidationError
import pandas as pd

class Team_issuance(models.Model):
    _inherit = 'stock.move'
    product_id_duplicate = fields.Many2one(related="product_id")
    product_id_refname = fields.Selection(related="product_id.product_tmpl_id.internal_ref_name")

    etsi_serials_field = fields.Char(string="Serial ID")
    etsi_mac_field = fields.Char(string="Mac ID")
    etsi_smart_card_field = fields.Char(string="Smart Card")

    # duplicate
    etsi_serials_field_duplicate = fields.Char(related="etsi_serials_field")
    etsi_mac_field_duplicate = fields.Char(related="etsi_mac_field")
    etsi_smart_card_field_duplicate = fields.Char(related="etsi_smart_card_field")

    uom_field_duplicate = fields.Many2one('product.uom',string="Unit of Measure",related="product_uom")
    uom_field_duplicate2 = fields.Many2one(related="uom_field_duplicate")
    # ,related="product_id_duplicate.product_tmpl_id.uom_id.id"
    checker_box = fields.Boolean(string="To be issued")

    issued_field = fields.Char(string="Status" , default="Available")
    subscriber_field = fields.Many2one('res.partner',string="Subcscriber")
    doc_source = fields.Many2one('stock.picking')

    etsi_description_txt = fields.Text(related='product_id.description_txt')  

    
    @api.multi
    @api.onchange('etsi_serials_field','etsi_mac_field','etsi_smart_card_field')
    def auto_fill_details_01(self): 
      
        
        for rec in self:
            database = self.env['etsi.inventory']
            database2 = self.env['product.template']
            drop_name = database2.search([('name','=',rec.etsi_serials_field)])
            duplicate_count = self.env['etsi.inventory'].search_count([('etsi_serial', '=', rec.etsi_serials_field)])
            duplicate_count2 = self.env['etsi.inventory'].search_count([('etsi_mac', '=', rec.etsi_mac_field)])
            duplicate_count3 = self.env['etsi.inventory'].search_count([('etsi_smart_card', '=', rec.etsi_smart_card_field)])
            search_first = database.search([('etsi_serial','=',rec.etsi_serials_field)])
            search_first2 = database.search([('etsi_mac','=',rec.etsi_mac_field)])
            search_first3 = database.search([('etsi_smart_card','=',rec.etsi_smart_card_field)])

            if rec.etsi_serials_field != False:
                if drop_name:
                    domain_check =[]

                    for rec2 in drop_name:
                        domain_check.append(rec2.uom_id.id)

                    if rec.etsi_serials_field != False and rec.uom_field_duplicate.id == False:
                        for rec3 in drop_name:
                            if rec3.internal_ref_name == 'drops' or rec3.internal_ref_name == 'others':
                                pass
                            else:
                                raise ValidationError("Material Code not found in the database.")
                    else:
                        raise ValidationError("Material Code not found in the database.")
                    
                    return{'domain': {'uom_field_duplicate':[('id','in',domain_check)]}}

                elif duplicate_count < 1:
                    raise ValidationError("Serial not found in the database.")
                else:
                    if search_first.etsi_status != 'available':
                        raise ValidationError("Serial is already used or currently on another transaction.")
                    else:
                        stock_moves = self.env['stock.move'].search([('state','not in',['cancel', 'done']),('picking_type_id.code','=','internal'),('picking_type_id.return_picking_type_id','!=',False)])

                        if stock_moves:
                            for moves in stock_moves:
                                if moves.etsi_serials_field == rec.etsi_serials_field:
                                    raise ValidationError("Serial is already on another process.")
                                else:
                                    test = database.search([('etsi_serial','=',rec.etsi_serials_field)])
                                    rec.product_id = test.etsi_product_id.id
                                    rec.etsi_serials_field = test.etsi_serial
                                    rec.etsi_mac_field = test.etsi_mac  
                                    rec.etsi_smart_card_field = test.etsi_smart_card
                                    rec.uom_field_duplicate = rec.product_uom.id
                        else:
                            test = database.search([('etsi_serial','=',rec.etsi_serials_field)])
                            rec.product_id = test.etsi_product_id.id
                            rec.etsi_serials_field = test.etsi_serial
                            rec.etsi_mac_field = test.etsi_mac  
                            rec.etsi_smart_card_field = test.etsi_smart_card
                            rec.uom_field_duplicate = rec.product_uom.id

               
            elif rec.etsi_mac_field != False:
                if duplicate_count2 < 1:
                    raise ValidationError("Mac not found in the database.")
                else:
                    if search_first2.etsi_status != 'available':
                        raise ValidationError("Mac is already used or currently on another transaction.")
                    else:
                        stock_moves = self.env['stock.move'].search([('state','not in',['cancel', 'done']),('picking_type_id.code','=','internal'),('picking_type_id.return_picking_type_id','!=',False),('issued_field','!=','Return')])

                        if stock_moves:
                            for moves in stock_moves:
                                if moves.etsi_mac_field == rec.etsi_mac_field:
                                    raise ValidationError("Mac is already on another process.")
                                else:
                                    test = database.search([('etsi_mac','=',rec.etsi_mac_field)])
                                    rec.product_id = test.etsi_product_id.id
                                    rec.etsi_serials_field = test.etsi_serial
                                    rec.etsi_mac_field = test.etsi_mac  
                                    rec.etsi_smart_card_field = test.etsi_smart_card
                                    rec.uom_field_duplicate = rec.product_uom.id
                        else:
                            test = database.search([('etsi_mac','=',rec.etsi_mac_field)])
                            rec.product_id = test.etsi_product_id.id
                            rec.etsi_serials_field = test.etsi_serial
                            rec.etsi_mac_field = test.etsi_mac  
                            rec.etsi_smart_card_field = test.etsi_smart_card
                            rec.uom_field_duplicate = rec.product_uom.id

            elif rec.etsi_smart_card_field != False:
                if duplicate_count3 < 1:
                    raise ValidationError("Smart Card not found in the database.")
                else:
                    if search_first3.etsi_status != 'available':
                        raise ValidationError("Smart Card is already used or currently on another transaction.")
                    else:
                        stock_moves = self.env['stock.move'].search([('state','not in',['cancel', 'done']),('picking_type_id.code','=','internal'),('picking_type_id.return_picking_type_id','!=',False),('issued_field','!=','Return')])

                        if stock_moves:
                            for moves in stock_moves:
                                if moves.etsi_smart_card_field == rec.etsi_smart_card_field:
                                    raise ValidationError("Smart card is already on another process.")
                                else:
                                    test = database.search([('etsi_smart_card','=',rec.etsi_smart_card_field)])
                                    rec.product_id = test.etsi_product_id.id
                                    rec.etsi_serials_field = test.etsi_serial
                                    rec.etsi_mac_field = test.etsi_mac  
                                    rec.etsi_smart_card_field = test.etsi_smart_card
                                    rec.uom_field_duplicate = rec.product_uom.id
                        else:
                            test = database.search([('etsi_smart_card','=',rec.etsi_smart_card_field)])
                            rec.product_id = test.etsi_product_id.id
                            rec.etsi_serials_field = test.etsi_serial
                            rec.etsi_mac_field = test.etsi_mac  
                            rec.etsi_smart_card_field = test.etsi_smart_card
                            rec.uom_field_duplicate = rec.product_uom.id
    
    @api.multi
    @api.onchange('uom_field_duplicate')
    def auto_fill_details_02(self): 
        for rec in self:
            if rec.etsi_serials_field != False and rec.uom_field_duplicate.id != False:
                database2 = self.env['product.template']
                drop_name2 = database2.search([('name','=',rec.etsi_serials_field),('uom_id','=',rec.uom_field_duplicate.id)])
                product2 = self.env['product.product'].browse(drop_name2.id)
                warehouse1_quantity2 = product2.with_context({'location' : 'WH/Stock'}).qty_available
                if drop_name2.internal_ref_name == 'drops' or drop_name2.internal_ref_name == 'others':
                    if warehouse1_quantity2 <= 0:
                        raise ValidationError("No stock available.")
                    else:
                        rec.product_id = drop_name2.id
                        rec.etsi_serials_field = False
                else:
                    pass

    @api.onchange('product_uom_qty')
    def check_stock_available(self):
        for rec in self:
            product = self.env['product.product'].browse(rec.product_id.id)
            warehouse1_quantity = product.with_context({'location' : 'WH/Stock'}).qty_available
            if rec.product_uom_qty != False and rec.product_id.id != False:
                if rec.product_uom_qty > warehouse1_quantity:
                    rec.product_uom_qty = 1
                    return {'warning': {'title': ('FlexERP Warning'), 'message': ('No stock available.'),},}
            else:
                pass
            
    @api.constrains('product_id')
    def testfunc312312(self):
        
        
        for record in self.picking_id.move_lines:
            if record.state == 'done':
                raise ValidationError("You cannot add new item once the record is validated.")

        check5 = self.picking_id.move_lines - self
        for rec2 in check5:
            # picking = self.env['stock.move'].search([('type_checker_02', '=' ,self.name)])
            if rec2.product_id.id == self.product_id.id:
                if rec2.etsi_serials_field == False and rec2.etsi_mac_field == False and rec2.etsi_smart_card_field == False:
                    check6 = "Duplicate Drops/Others detected within the Table \n: {}".format(rec2.product_id.product_tmpl_id.name)
                    if self.picking_id.teller == 'others':
                         
                        raise ValidationError(check6)

    @api.constrains('etsi_serials_field')
    def testfunc(self):
        for record in self.picking_id.move_lines:
            if record.state == 'done':
                raise ValidationError("You cannot add new item once the record is validated.")

        check5 = self.picking_id.move_lines - self
        for rec2 in check5:
            if self.etsi_serials_field == False:
                print("running")
                pass
            elif rec2.etsi_serials_field == self.etsi_serials_field:
                check6 = "Duplicate detected within the Table \n Serial Number: {}".format(rec2.etsi_serials_field)
                raise ValidationError(check6)
        
    @api.constrains('etsi_mac_field')
    def testfunc2(self):
        for record in self.picking_id.move_lines:
            if record.state == 'done':
                raise ValidationError("You cannot add new item once the record is validated.")

        check5 = self.picking_id.move_lines - self
        for rec2 in check5:
            if self.etsi_mac_field == False:
                print("running")
                pass
            elif rec2.etsi_mac_field == self.etsi_mac_field:
                check6 = "Duplicate detected within the Table \n Mac Number: {}".format(rec2.etsi_serials_field)
                raise ValidationError(check6)
    
    @api.constrains('etsi_smart_card_field')
    def testfunc3(self):
        for record in self.picking_id.move_lines:
            if record.state == 'done':
                raise ValidationError("You cannot add new item once the record is validated.")
                
        check5 = self.picking_id.move_lines - self
        for rec2 in check5:
            if self.etsi_smart_card_field == False:
                print("running")
                pass
            elif rec2.etsi_smart_card_field == self.etsi_smart_card_field:
                check6 = "Duplicate detected within the Table \n Smart Card Number: {}".format(rec2.etsi_serials_field)
                raise ValidationError(check6)

class Team_issuance_stock_picking(models.Model):
    _inherit = 'stock.picking'

    move_lines = fields.One2many('stock.move', 'picking_id', string="Stock Moves", copy=True)
    line = fields.Many2one("team.configuration")

    @api.multi
    @api.onchange('move_lines')
    def lalala(self):
        list_original_serials = []  
        list_original_mac = []  
        list_original_smart= []  
        list_multiple_drop= []  
        for rec in self:
            for line in self.move_lines:
                if not line.etsi_serials_field_duplicate == False:
                    list_original_serials.append(line.etsi_serials_field_duplicate)
                if not line.etsi_mac_field_duplicate == False:
                    list_original_serials.append(line.etsi_mac_field_duplicate)
                if not line.etsi_smart_card_field_duplicate == False:
                    list_original_serials.append(line.etsi_smart_card_field_duplicate)
                if line.etsi_smart_card_field_duplicate == False and line.etsi_smart_card_field_duplicate == False and line.etsi_serials_field_duplicate == False:
                    list_multiple_drop.append(line.product_id.id)

        df_serials = pd.DataFrame(list_original_serials)
        df_mac = pd.DataFrame(list_original_mac)
        df_smart = pd.DataFrame(list_original_smart)
        df_drop = pd.DataFrame(list_multiple_drop)

        duplicate_serials = df_serials[df_serials.duplicated()]
        duplicate_mac = df_mac[df_mac.duplicated()]
        duplicate_smart = df_smart[df_smart.duplicated()]
        duplicate_drop = df_drop[df_drop.duplicated()]

        if not duplicate_serials.empty:
            return {'warning': {'title': _('Warning'),'message': _('Duplicate Serials Detected within the table.')}}
        elif not duplicate_mac.empty:
            return {'warning': {'title': _('Warning'),'message': _('Duplicate Mac Detected within the table.')}}
        elif not duplicate_smart.empty:
            return {'warning': {'title': _('Warning'),'message': _('Duplicate Smart Card Detected within the table.')}}
        elif not duplicate_drop.empty:
            return {'warning': {'title': _('Warning'),'message': _('Duplicate Drops Detected within the table.')}}

    @api.multi
    def process(self):
        self.ensure_one()
        for pack in self.pack_operation_product_ids:
            if pack.product_qty > 0:
                pack.write({'qty_done': pack.product_qty})
            else:
                pack.unlink()
        return 

    @api.multi
    def do_transfer(self):
        res = super(Team_issuance_stock_picking, self).do_transfer()

        for check in self:
            # picking_checker = self.env['stock.picking.type'].search([('name', '=', 'Subscriber Issuance')])
            picking_checker = self.env['stock.picking.type'].search([('code', '=', 'internal'),('return_picking_type_id','!=',False)])
            
            if self.picking_type_id.id == picking_checker.id:
                for rec in self.move_lines:
                    if rec.etsi_serials_field != False:
                        status_checker = self.env['etsi.inventory'].search([('etsi_serial', '=', rec.etsi_serials_field)])
                        status_checker.etsi_status = "deployed"
                        status_checker.etsi_team_in = self.etsi_teams_id.id

                        status_checker2 = self.env['stock.move'].search([('etsi_serials_field', '=', rec.etsi_serials_field)])
                        picking_id_checker = self.env['stock.picking'].search([('name', '=', self.name)])
                        status_checker.write({'etsi_history_lines': [(0,0, {'etsi_history_quantity':rec.product_uom_qty,'etsi_operation':'Team Issuance','etsi_transaction_description':'Warehouse to Team Location','etsi_transaction_num':picking_id_checker.id,'etsi_action_date':self.min_date,'etsi_status':'Deployed','etsi_employee':self.env.user.id,'etsi_teams':self.etsi_teams_id.id})]})

                        for records in status_checker2:
                                records.issued_field = "Deployed"
                                records.doc_source = check.id
                                # records.checker_box = False
                    elif rec.etsi_serials_field == False and rec.product_id_duplicate.id != False:
                        rec.issued_field = "Deployed"
                        picking_id_checker = self.env['stock.picking'].search([('name', '=', self.name)])
                        checker = self.env['etsi.inventory'].search([('etsi_team_in', '=', self.etsi_teams_id.id),('type_checker', '=', 'drops'),('etsi_product_id', '=', rec.product_id_duplicate.id)])
                        quantity_result = checker.etsi_product_quantity + rec.product_uom_qty

                       
                        if checker:
                            
                            checker.update({
                                'type_checker_02':rec.product_id_duplicate.internal_ref_name,
                                'etsi_product_id':rec.product_id_duplicate.id,
                                'etsi_product_name':rec.product_id_duplicate.id,
                                'etsi_product_quantity': quantity_result,
                                'etsi_team_in': self.etsi_teams_id.id,
                                'etsi_employee_in': self.env.user.id,
                                'etsi_status':"deployed",
                            })
                            checker.write({'etsi_history_lines': [(0,0, {'etsi_history_quantity':rec.product_uom_qty,'etsi_operation':'Team Issuance','etsi_transaction_description':'Warehouse to Team Location','etsi_transaction_num':picking_id_checker.id,'etsi_action_date':self.min_date,'etsi_status':'Deployed','etsi_employee':self.env.user.id,'etsi_teams':self.etsi_teams_id.id})]})
                        else:
                            lst = []
                            res = {'etsi_history_quantity':rec.product_uom_qty,'etsi_operation':'Team Issuance','etsi_transaction_description':'Warehouse to Team Location','etsi_transaction_num':picking_id_checker.id,'etsi_action_date':self.min_date,'etsi_status':'Deployed','etsi_employee':self.env.user.id,'etsi_teams':self.etsi_teams_id.id}
                            lst.append(res)
                            new_lst = []
                            for x in lst:
                                new_lst.append((0, 0, x))

                            self.env['etsi.inventory'].create({
                                'type_checker_02':rec.product_id_duplicate.internal_ref_name,
                                'etsi_product_id':rec.product_id_duplicate.id,
                                'etsi_product_name':rec.product_id_duplicate.id,
                                'etsi_product_quantity': quantity_result,
                                'etsi_team_in': self.etsi_teams_id.id,
                                'etsi_employee_in': self.env.user.id,
                                'etsi_history_lines': new_lst,
                                'etsi_status':"deployed",
                            })
            else:
                pass
        return res