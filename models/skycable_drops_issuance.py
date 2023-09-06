from odoo import api, fields, models, _
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from odoo.exceptions import ValidationError, UserError
import xlsxwriter, base64
from xlsxwriter.utility import xl_rowcol_to_cell
from tempfile import TemporaryFile
import io
from xlrd import open_workbook
import csv
import chardet
import codecs
import pandas as pd

class Drops_Issuance(models.Model):
    _name = "stock.drops.issuance"

    # Transaction info
    callid = fields.Char(string="Job Order")
    import_batch = fields.Char(string="Import Batch Name")
    employee_name = fields.Many2one('res.users', string='Employee Name', default=lambda self: self.env.user.id)
    date_time = fields.Date(string="Date Imported", default=fields.Datetime.now)
    stats = fields.Selection([
        ('draft','Draft'),
        ('done','Done')
    ], string="Status", default="draft")
    task_type_category = fields.Char(string="Task Type Category")
    assigned_engineer  = fields.Many2one('team.configuration',string="Teams")
    completion_date = fields.Date(string="Completion Date")
    ref_number = fields.Many2one('stock.picking', string="Reference Number")
    counter_drops = fields.Integer("Available Drops")

    # Drops - names
    rg_6_cable_black_wo_mess = fields.Char('RG-6 CABLE BLACK W/O MESS', default="RG-6 CABLE BLACK W/O MESS") 
    rg_6_cable_black_w_mess = fields.Char('RG-6 CABLE BLACK W/ MESS', default="RG-6 CABLE BLACK W/ MESS")
    rg_6_connector = fields.Char('RG-6 CONNECTOR', default="RG-6 CONNECTOR")
    ground_block = fields.Char('GROUND BLOCK', default="GROUND BLOCK")
    two_way_splitter = fields.Char('2 WAY SPLITTER', default="2 WAY SPLITTER")
    ground_rod = fields.Char('GROUND ROD', default="GROUND ROD")
    span_clamp = fields.Char('SPAN CLAMP', default="SPAN CLAMP")
    high_pass_filter = fields.Char('HIGH PASS FILTER', default="HIGH PASS FILTER")
    isolator = fields.Char('ISOLATOR', default="ISOLATOR")
    ground_clamp = fields.Char('GROUND CLAMP', default="GROUND CLAMP")
    attenuator_3db = fields.Char('ATTENUATOR 3dB', default="ATTENUATOR 3dB")
    attenuator_6db = fields.Char('ATTENUATOR 6dB', default="ATTENUATOR 6dB")
    cable_clip = fields.Char('CABLE CLIP', default="CABLE CLIP")
    cable_tag = fields.Char('CABLE TAG', default="CABLE TAG")
    f_81_connector = fields.Char('F-81 CONNECTOR', default="F-81 CONNECTOR")
    fiber_optic_apc_connector = fields.Char('FIBER OPTIC APC CONNECTOR', default="FIBER OPTIC APC CONNECTOR")
    fiber_optic_patch_cord_bipc_2mtrs = fields.Char('FIBER OPTIC PATCH CORD BIPC 2mtrs', default="FIBER OPTIC PATCH CORD BIPC 2mtrs")
    fiber_optic_patch_cord_sc_apc_to_sc_apc_3mtrs = fields.Char('FIBER OPTIC PATCH CORD SC/APC to SC/APC 3mtrs', default="FIBER OPTIC PATCH CORD SC/APC to SC/APC 3mtrs")
    fiber_optic_patch_cord_sc_apc_to_sc_apc_6mtrs = fields.Char('FIBER OPTIC PATCH CORD SC/APC to SC/APC 6mtrs', default="FIBER OPTIC PATCH CORD SC/APC to SC/APC 6mtrs")
    ground_wire = fields.Char('GROUND WIRE', default="GROUND WIRE")
    p_hook = fields.Char('P-HOOK', default="P-HOOK")
    rg_11_cable_w_mess = fields.Char('RG-11 CABLE W/ MESS', default="RG-11 CABLE W/ MESS")
    rg_11_connector = fields.Char('RG-11 CONNECTOR', default="RG-11 CONNECTOR")
    utp_cable_1_meter = fields.Char('UTP CABLE 1 meter', default="UTP CABLE 1 meter")

    # Drops - quantity
    rg_6_cable_black_wo_mess_qty = fields.Integer() 
    rg_6_cable_black_w_mess_qty = fields.Integer()
    rg_6_connector_qty = fields.Integer()
    ground_block_qty = fields.Integer()
    two_way_splitter_qty = fields.Integer()
    ground_rod_qty = fields.Integer()
    span_clamp_qty = fields.Integer()
    high_pass_filter_qty = fields.Integer()
    isolator_qty = fields.Integer()
    ground_clamp_qty = fields.Integer()
    attenuator_3db_qty = fields.Integer()
    attenuator_6db_qty = fields.Integer()
    cable_clip_qty = fields.Integer()
    cable_tag_qty = fields.Integer()
    f_81_connector_qty = fields.Integer()
    fiber_optic_apc_connector_qty = fields.Integer()
    fiber_optic_patch_cord_bipc_2mtrs_qty = fields.Integer()
    fiber_optic_patch_cord_sc_apc_to_sc_apc_3mtrs_qty = fields.Integer()
    fiber_optic_patch_cord_sc_apc_to_sc_apc_6mtrs_qty = fields.Integer()
    ground_wire_qty = fields.Integer()
    p_hook_qty = fields.Integer()
    rg_11_cable_w_mess_qty = fields.Integer()
    rg_11_connector_qty = fields.Integer()
    utp_cable_1_meter_qty = fields.Integer()

class Drops_Issuance_Import(models.TransientModel):
    _name = "stock.drops.import"
    final_batch = ""

    import_batch = fields.Char(string="Import Batch Name")
    import_batch_duplicate = fields.Char(string="Import Batch Name", related='import_batch')
    data = fields.Binary()
    employee_name = fields.Many2one('res.users', string='Employee Name', default=lambda self: self.env.user.id)
    date_time = fields.Date(string="Date Imported", default=fields.Datetime.now)

    @api.multi
    def run_validate(self):
        # Run validate function
        self.drop_validate()

        search_job_number = self.env['stock.drops.issuance'].search([('import_batch', '=', self.final_batch)])
        search_product = self.env['product.template'].search([])
        search_product_id  = self.env['product.product'].search([])
        count = 0
        listahan = []

        if search_job_number:
            for item in search_job_number:
                if item.rg_6_cable_black_wo_mess_qty > 0 :
                    for laman in search_product:
                        if laman.clicksolf_code == 'RG-6 CABLE BLACK W/O MESS':
                            searched_id = 0
                            description = ""
                            for prod_id in search_product_id:
                                if prod_id.id == laman.id:
                                    searched_id = prod_id.id
                                    description = laman.description_txt
                                    product_clicksolf_code = laman.clicksolf_code
                    
                                    count += 1
                                    listahan.append(( 0,0, {
                                        'job_number' : item.callid, 
                                        'product_clicksolf_code' : product_clicksolf_code,
                                        'clicksolf_quantity' : item.rg_6_cable_black_wo_mess_qty,
                                        'product_id' : searched_id,
                                        'product_description' : description, 
                                        'product_uom' : laman.uom_id.id, 
                                        'clicksolf_team' : item.assigned_engineer.id,
                                    }))

                if item.rg_6_cable_black_w_mess_qty > 0 :
                    for laman in search_product:
                        if laman.clicksolf_code == 'RG-6 CABLE BLACK W/ MESS':
                            searched_id = 0
                            description = ""
                            for prod_id in search_product_id:
                                if prod_id.id == laman.id:
                                    searched_id = prod_id.id
                                    description = laman.description_txt
                                    product_clicksolf_code = laman.clicksolf_code
                    
                                    count += 1
                                    listahan.append(( 0,0, {
                                        'job_number' : item.callid, 
                                        'product_clicksolf_code' : product_clicksolf_code,
                                        'clicksolf_quantity' : item.rg_6_cable_black_w_mess_qty,
                                        'product_id' : searched_id,
                                        'product_description' : description, 
                                        'product_uom' : laman.uom_id.id, 
                                        'clicksolf_team' : item.assigned_engineer.id
                                    }))
                    
                if item.rg_6_connector_qty > 0 :
                    for laman in search_product:
                        if laman.clicksolf_code == 'RG-6 CONNECTOR':
                            searched_id = 0
                            description = ""
                            for prod_id in search_product_id:
                                if prod_id.id == laman.id:
                                    searched_id = prod_id.id
                                    description = laman.description_txt
                                    product_clicksolf_code = laman.clicksolf_code
                    
                                    count += 1
                                    listahan.append(( 0,0, {
                                        'job_number' : item.callid, 
                                        'product_clicksolf_code' : product_clicksolf_code,
                                        'clicksolf_quantity' : item.rg_6_connector_qty,
                                        'product_id' : searched_id,
                                        'product_description' : description, 
                                        'product_uom' : laman.uom_id.id, 
                                        'clicksolf_team' : item.assigned_engineer.id
                                    }))
                
                if item.ground_block_qty > 0 :
                    for laman in search_product:
                        if laman.clicksolf_code == 'GROUND BLOCK':
                            searched_id = 0
                            description = ""
                            for prod_id in search_product_id:
                                if prod_id.id == laman.id:
                                    searched_id = prod_id.id
                                    description = laman.description_txt
                                    product_clicksolf_code = laman.clicksolf_code
                    
                                    count += 1
                                    listahan.append(( 0,0, {
                                        'job_number' : item.callid, 
                                        'product_clicksolf_code' : product_clicksolf_code,
                                        'clicksolf_quantity' : item.ground_block_qty,
                                        'product_id' : searched_id,
                                        'product_description' : description, 
                                        'product_uom' : laman.uom_id.id, 
                                        'clicksolf_team' : item.assigned_engineer.id 
                                        
                                    }))
                                
                if item.two_way_splitter_qty > 0 :
                    for laman in search_product:
                        if laman.clicksolf_code == '2 WAY SPLITTER':
                            searched_id = 0
                            description = ""
                            for prod_id in search_product_id:
                                if prod_id.id == laman.id:
                                    searched_id = prod_id.id
                                    description = laman.description_txt
                                    product_clicksolf_code = laman.clicksolf_code
                    
                                    count += 1
                                    listahan.append(( 0,0, {
                                        'job_number' : item.callid, 
                                        'product_clicksolf_code' : product_clicksolf_code,
                                        'clicksolf_quantity' : item.two_way_splitter_qty,
                                        'product_id' : searched_id,
                                        'product_description' : description, 
                                        'product_uom' : laman.uom_id.id, 
                                        'clicksolf_team' : item.assigned_engineer.id
                                    }))
                    
                if item.ground_rod_qty > 0 :
                    for laman in search_product:
                        if laman.clicksolf_code == 'GROUND ROD':
                            searched_id = 0
                            description = ""
                            for prod_id in search_product_id:
                                if prod_id.id == laman.id:
                                    searched_id = prod_id.id
                                    description = laman.description_txt
                                    product_clicksolf_code = laman.clicksolf_code
                    
                                    count += 1
                                    listahan.append(( 0,0, {
                                        'job_number' : item.callid, 
                                        'product_clicksolf_code' : product_clicksolf_code,
                                        'clicksolf_quantity' : item.ground_rod_qty,
                                        'product_id' : searched_id,
                                        'product_description' : description, 
                                        'product_uom' : laman.uom_id.id, 
                                        'clicksolf_team' : item.assigned_engineer.id
                                    }))

                if item.span_clamp_qty > 0:
                    for laman in search_product:
                        if laman.clicksolf_code == 'SPAN CLAMP':
                            searched_id = 0
                            description = ""
                            for prod_id in search_product_id:
                                if prod_id.id == laman.id:
                                    searched_id = prod_id.id
                                    description = laman.description_txt
                                    product_clicksolf_code = laman.clicksolf_code
                    
                                    count += 1
                                    listahan.append(( 0,0, {
                                        'job_number' : item.callid,
                                        'product_clicksolf_code' : product_clicksolf_code, 
                                        'clicksolf_quantity' : item.span_clamp_qty,
                                        'product_id' : searched_id,
                                        'product_description' : description, 
                                        'product_uom' : laman.uom_id.id, 
                                        'clicksolf_team' : item.assigned_engineer.id
                                    }))
                                            
                if item.high_pass_filter_qty > 0:
                    for laman in search_product:
                        if laman.clicksolf_code == 'HIGH PASS FILTER':
                            searched_id = 0
                            description = ""
                            for prod_id in search_product_id:
                                if prod_id.id == laman.id:
                                    searched_id = prod_id.id
                                    description = laman.description_txt
                                    product_clicksolf_code = laman.clicksolf_code
                            
                                    count += 1
                                    listahan.append(( 0,0, {
                                        'job_number' : item.callid, 
                                        'product_clicksolf_code' : product_clicksolf_code,
                                        'clicksolf_quantity' : item.high_pass_filter_qty,
                                        'product_id' : searched_id,
                                        'product_description' : description, 
                                        'product_uom' : laman.uom_id.id, 
                                        'clicksolf_team' : item.assigned_engineer.id
                                        
                                    }))
                
                
                if item.isolator_qty > 0:
                    for laman in search_product:
                        if laman.clicksolf_code == 'ISOLATOR':
                            searched_id = 0
                            description = ""
                            for prod_id in search_product_id:
                                if prod_id.id == laman.id:
                                    searched_id = prod_id.id
                                    description = laman.description_txt
                                    product_clicksolf_code = laman.clicksolf_code
                    
                                    count += 1
                                    listahan.append(( 0,0, {
                                        'job_number' : item.callid, 
                                        'product_clicksolf_code' : product_clicksolf_code,
                                        'clicksolf_quantity' : item.isolator_qty,
                                        'product_id' : searched_id,
                                        'product_description' : description, 
                                        'clicksolf_team' : item.assigned_engineer.id,
                                        'product_uom' : laman.uom_id.id, 
                                    }))
                
                if item.ground_clamp_qty > 0:
                    for laman in search_product:
                        if laman.clicksolf_code == 'GROUND CLAMP':
                            searched_id = 0
                            description = ""
                            for prod_id in search_product_id:
                                if prod_id.id == laman.id:
                                    searched_id = prod_id.id
                                    description = laman.description_txt
                                    product_clicksolf_code = laman.clicksolf_code
                    
                                    count += 1
                                    listahan.append(( 0,0, {
                                        'job_number' : item.callid,
                                        'product_clicksolf_code' : product_clicksolf_code, 
                                        'clicksolf_quantity' : item.ground_clamp_qty,
                                        'product_id' : searched_id,
                                        'product_description' : description, 
                                        'product_uom' : laman.uom_id.id, 
                                        'clicksolf_team' : item.assigned_engineer.id
                                    }))
                
                if item.attenuator_3db_qty > 0:
                    for laman in search_product:
                        if laman.clicksolf_code == 'ATTENUATOR 3dB':
                            searched_id = 0
                            description = ""
                            for prod_id in search_product_id:
                                if prod_id.id == laman.id:
                                    searched_id = prod_id.id
                                    description = laman.description_txt
                                    product_clicksolf_code = laman.clicksolf_code
                                    
                                    count += 1
                                    listahan.append(( 0,0, {
                                        'job_number' : item.callid, 
                                        'product_clicksolf_code' : product_clicksolf_code,
                                        'clicksolf_quantity' : item.attenuator_3db_qty,
                                        'product_id' : searched_id,
                                        'product_description' : description, 
                                        'product_uom' : laman.uom_id.id, 
                                        'clicksolf_team' : item.assigned_engineer.id
                                    }))
                    
                
                if item.attenuator_6db_qty > 0:
                    for laman in search_product:
                        if laman.clicksolf_code == 'ATTENUATOR 6dB':
                            searched_id = 0
                            description = ""
                            for prod_id in search_product_id:
                                if prod_id.id == laman.id:
                                    searched_id = prod_id.id
                                    description = laman.description_txt
                                    product_clicksolf_code = laman.clicksolf_code
                    
                                    count += 1
                                    listahan.append(( 0,0, {
                                        'job_number' : item.callid, 
                                        'product_clicksolf_code' : product_clicksolf_code,
                                        'clicksolf_quantity' : item.attenuator_6db_qty,
                                        'product_id' : searched_id,
                                        'product_description' : description, 
                                        'product_uom' : laman.uom_id.id, 
                                        'clicksolf_team' : item.assigned_engineer.id
                                    }))
                
                
                if item.cable_clip_qty > 0:
                    for laman in search_product:
                        if laman.clicksolf_code == 'CABLE CLIP':
                            searched_id = 0
                            description = ""
                            for prod_id in search_product_id:
                                if prod_id.id == laman.id:
                                    searched_id = prod_id.id
                                    description = laman.description_txt
                                    product_clicksolf_code = laman.clicksolf_code
                    
                                    count += 1
                                    listahan.append(( 0,0, {
                                        'job_number' : item.callid,
                                        'product_clicksolf_code' : product_clicksolf_code,
                                        'clicksolf_quantity' : item.cable_clip_qty,
                                        'product_id' : searched_id,
                                        'product_description' : description, 
                                        'product_uom' : laman.uom_id.id, 
                                        'clicksolf_team' : item.assigned_engineer.id
                                    }))
                
                if item.cable_tag_qty > 0:
                    for laman in search_product:
                        if laman.clicksolf_code == 'CABLE TAG':
                            searched_id = 0
                            description = ""
                            for prod_id in search_product_id:
                                if prod_id.id == laman.id:
                                    searched_id = prod_id.id
                                    description = laman.description_txt
                                    product_clicksolf_code = laman.clicksolf_code
                    
                                    count += 1
                                    listahan.append(( 0,0, {
                                        'job_number' : item.callid, 
                                        'product_clicksolf_code' : product_clicksolf_code,
                                        'clicksolf_quantity' : item.cable_tag_qty,
                                        'product_id' : searched_id,
                                        'product_description' : description, 
                                        'product_uom' : laman.uom_id.id, 
                                        'clicksolf_team' : item.assigned_engineer.id
                                    }))
                
                if item.f_81_connector_qty > 0:
                    for laman in search_product:
                        if laman.clicksolf_code == 'F-81 CONNECTOR':
                            searched_id = 0
                            description = ""
                            for prod_id in search_product_id:
                                if prod_id.id == laman.id:
                                    searched_id = prod_id.id
                                    description = laman.description_txt
                                    product_clicksolf_code = laman.clicksolf_code
                            
                                    count += 1
                                    listahan.append(( 0,0, {
                                        'job_number' : item.callid, 
                                        'product_clicksolf_code' : product_clicksolf_code,
                                        'clicksolf_quantity' : item.f_81_connector_qty,
                                        'product_id' : searched_id,
                                        'product_description' : description, 
                                        'product_uom' : laman.uom_id.id, 
                                        'clicksolf_team' : item.assigned_engineer.id
                                    }))
                
                if item.fiber_optic_apc_connector_qty > 0:
                    for laman in search_product:
                        if laman.clicksolf_code == 'FIBER OPTIC APC CONNECTOR':
                            searched_id = 0
                            description = ""
                            for prod_id in search_product_id:
                                if prod_id.id == laman.id:
                                    searched_id = prod_id.id
                                    description = laman.description_txt
                                    product_clicksolf_code = laman.clicksolf_code
                            
                                    count += 1
                                    listahan.append(( 0,0, {
                                        'job_number' : item.callid, 
                                        'product_clicksolf_code' : product_clicksolf_code,
                                        'clicksolf_quantity' : item.fiber_optic_apc_connector_qty,
                                        'product_id' : searched_id,
                                        'product_description' : description, 
                                        'product_uom' : laman.uom_id.id, 
                                        'clicksolf_team' : item.assigned_engineer.id
                                    }))
                    
                
                if item.fiber_optic_patch_cord_bipc_2mtrs_qty> 0:
                    for laman in search_product:
                        if laman.clicksolf_code == 'FIBER OPTIC PATCH CORD BIPC 2mtrs':
                            searched_id = 0
                            description = ""
                            for prod_id in search_product_id:
                                if prod_id.id == laman.id:
                                    searched_id = prod_id.id
                                    description = laman.description_txt
                                    product_clicksolf_code = laman.clicksolf_code
                    
                                    count += 1
                                    listahan.append(( 0,0, {
                                        'job_number' : item.callid,
                                        'product_clicksolf_code' : product_clicksolf_code, 
                                        'clicksolf_quantity' : item.fiber_optic_patch_cord_bipc_2mtrs_qty,
                                        'product_id' : searched_id,
                                        'product_description' : description, 
                                        'product_uom' : laman.uom_id.id, 
                                        'clicksolf_team' : item.assigned_engineer.id
                                    }))

                if item.fiber_optic_patch_cord_sc_apc_to_sc_apc_3mtrs_qty> 0:
                    for laman in search_product:
                        if laman.clicksolf_code == 'FIBER OPTIC PATCH CORD SC/APC to SC/APC 3mtrs':
                            searched_id = 0
                            description = ""
                            for prod_id in search_product_id:
                                if prod_id.id == laman.id:
                                    searched_id = prod_id.id
                                    description = laman.description_txt
                                    product_clicksolf_code = laman.clicksolf_code
                    
                                    count += 1
                                    listahan.append(( 0,0, {
                                        'job_number' : item.callid,
                                        'product_clicksolf_code' : product_clicksolf_code,
                                        'clicksolf_quantity' : item.fiber_optic_patch_cord_sc_apc_to_sc_apc_3mtrs_qty,
                                        'product_id' : searched_id,
                                        'product_description' : description, 
                                        'product_uom' : laman.uom_id.id, 
                                        'clicksolf_team' : item.assigned_engineer.id
                                    }))
                    
                    
                if item.fiber_optic_patch_cord_sc_apc_to_sc_apc_6mtrs_qty> 0:
                    for laman in search_product:
                        if laman.clicksolf_code == 'FIBER OPTIC PATCH CORD SC/APC to SC/APC 6mtrs':
                            searched_id = 0
                            description = ""
                            for prod_id in search_product_id:
                                if prod_id.id == laman.id:
                                    searched_id = prod_id.id
                                    description = laman.description_txt
                                    product_clicksolf_code = laman.clicksolf_code
                                    
                                    count += 1
                                    listahan.append(( 0,0, {
                                        'job_number' : item.callid, 
                                        'product_clicksolf_code' : product_clicksolf_code,
                                        'clicksolf_quantity' : item.fiber_optic_patch_cord_sc_apc_to_sc_apc_6mtrs_qty,
                                        'product_id' : searched_id,
                                        'product_description' : description, 
                                        'product_uom' : laman.uom_id.id,  
                                        'clicksolf_team' : item.assigned_engineer.id
                                    }))
                                    
                if item.ground_wire_qty > 0:
                    for laman in search_product:
                        if laman.clicksolf_code == 'GROUND WIRE':
                            searched_id = 0
                            description = ""
                            for prod_id in search_product_id:
                                if prod_id.id == laman.id:
                                    searched_id = prod_id.id
                                    description = laman.description_txt
                                    product_clicksolf_code = laman.clicksolf_code
                    
                                    count += 1
                                    listahan.append(( 0,0, {
                                        'job_number' : item.callid, 
                                        'product_clicksolf_code' : product_clicksolf_code,
                                        'clicksolf_quantity' : item.ground_wire_qty,
                                        'product_id' : searched_id,
                                        'product_description' : description, 
                                        'product_uom' : laman.uom_id.id,  
                                        'clicksolf_team' : item.assigned_engineer.id
                                    }))
                    
                
                if item.p_hook_qty > 0:
                    for laman in search_product:
                        if laman.clicksolf_code == 'P-HOOK':
                            searched_id = 0
                            description = ""
                            for prod_id in search_product_id:
                                if prod_id.id == laman.id:
                                    searched_id = prod_id.id
                                    description = laman.description_txt
                                    product_clicksolf_code = laman.clicksolf_code
                    
                                    count += 1
                                    listahan.append(( 0,0, {
                                        'job_number' : item.callid,
                                        'product_clicksolf_code' : product_clicksolf_code,
                                        'clicksolf_quantity' : item.p_hook_qty,
                                        'product_id' : searched_id,
                                        'product_description' : description, 
                                        'product_uom' : laman.uom_id.id,  
                                        'clicksolf_team' : item.assigned_engineer.id
                                    }))
                
                if item.rg_11_cable_w_mess_qty > 0:
                    for laman in search_product:
                        if laman.clicksolf_code == 'RG-11 CABLE W/ MESS':
                            searched_id = 0
                            description = ""
                            for prod_id in search_product_id:
                                if prod_id.id == laman.id:
                                    searched_id = prod_id.id
                                    description = laman.description_txt
                                    product_clicksolf_code = laman.clicksolf_code
                                    
                                    count += 1
                                    listahan.append(( 0,0, {
                                        'job_number' : item.callid, 
                                        'product_clicksolf_code' : product_clicksolf_code,
                                        'clicksolf_quantity' : item.rg_11_cable_w_mess_qty,
                                        'product_id' : searched_id,
                                        'product_description' : description, 
                                        'product_uom' : laman.uom_id.id,  
                                        'clicksolf_team' : item.assigned_engineer.id
                                    }))
                
                if item.rg_11_connector_qty > 0:
                    for laman in search_product:
                        if laman.clicksolf_code == 'RG-11 CONNECTOR':
                            searched_id = 0
                            description = ""
                            for prod_id in search_product_id:
                                if prod_id.id == laman.id:
                                    searched_id = prod_id.id
                                    description = laman.description_txt
                                    product_clicksolf_code = laman.clicksolf_code
                    
                                    count += 1
                                    listahan.append(( 0,0, {
                                        'job_number' : item.callid, 
                                        'product_clicksolf_code' : product_clicksolf_code,
                                        'clicksolf_quantity' : item.rg_11_connector_qty,
                                        'product_id' : searched_id,
                                        'product_description' : description, 
                                        'clicksolf_team' : item.assigned_engineer.id,
                                        'product_uom' : laman.uom_id.id,  
                                    }))
                
                if item.utp_cable_1_meter_qty > 0:
                    for laman in search_product:
                        if laman.clicksolf_code == 'UTP CABLE 1 meter':
                            searched_id = 0
                            description = ""
                            for prod_id in search_product_id:
                                if prod_id.id == laman.id:
                                    searched_id = prod_id.id
                                    description = laman.description_txt
                                    product_clicksolf_code = laman.clicksolf_code
                                    
                                    count += 1
                                    listahan.append(( 0,0, {
                                        'job_number' : item.callid, 
                                        'product_clicksolf_code' : product_clicksolf_code,
                                        'clicksolf_quantity' : item.utp_cable_1_meter_qty,
                                        'product_id' : searched_id,
                                        'product_description' : description, 
                                        'product_uom' : laman.uom_id.id,  
                                        'clicksolf_team' : item.assigned_engineer.id
                                    }))
                # Pass the counter value
                # item.counter_drops = count

        # self.update({'drops_issue' : listahan})
        picking_checker = self.env['stock.picking.type'].search([('code', '=', 'outgoing'),('subscriber_checkbox', '=', True)])
        get_all_data = self.env['stock.picking']

        runfunctiontest = get_all_data.create({
            'picking_type_id': picking_checker.id,
            # 'move_lines': [],
            'location_id': picking_checker.default_location_src_id.id,
            'location_dest_id': picking_checker.default_location_dest_id.id,
            'drops_issue': listahan,
            'teller':'subscriber'
        })

        search_picking = self.env['stock.picking'].search([('name', '=', runfunctiontest.name)])
        batch_updater = self.env['stock.drops.issuance'].search([('import_batch', '=', self.final_batch)])
        if batch_updater:
            for record in batch_updater:
                record.ref_number = search_picking.id

        return {
            'name': _("Subscriber Issuance"),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': runfunctiontest.id,
            'target': 'current',
        }

    @api.multi
    def drop_validate(self): 
        for rec in self:
            error = False
            if rec.data == None or rec.employee_name == "" or rec.date_time == "":
                error = True
                if error == True:
                    raise ValidationError('Fill all fields in this form!')
            
            # Mandatory fields
            if rec.data:
                # Decode the base64 encoded data and create a file-like object
                data_file = io.BytesIO(base64.b64decode(self.data))

                # Create an IncrementalDecoder for UTF-8
                decoder = codecs.getincrementaldecoder('utf-8')

                # Read the data from the file in chunks
                chunk = data_file.read(1024)
                text = ''
                
                while chunk:
                    # Decode the chunk using the IncrementalDecoder
                    text += chunk
                    # Read the next chunk
                    chunk = data_file.read(1024)

                # Use the csv.reader function to process the rows
                csv_reader = csv.reader(text.splitlines(), delimiter=',')

                data_list=[]
                row_num = 0

                # Drops - Names
                drops_names = []
                team_names = []
                drop1 = 0
                drop2 = 0
                drop3 = 0
                drop4 = 0
                drop5 = 0
                drop6 = 0
                drop7 = 0
                drop8 = 0
                drop9 = 0
                drop10 = 0
                drop11 = 0
                drop12 = 0
                drop13 = 0
                drop14 = 0
                drop15 = 0
                drop16 = 0
                drop17 = 0
                drop18 = 0
                drop19 = 0
                drop20 = 0
                drop21 = 0
                drop22 = 0
                drop23 = 0
                drop24 = 0

                for row in csv_reader:
                    row_num += 1
                    data_dict={}
                    # Transaction Info - Values
                    callid_value = ''
                    task_type_category_value = ''
                    assigned_engineer_value = ''
                    completion_date_value = ''

                    # Transaction Info - Values
                    callid = row[0]
                    task_type_category = row[6]
                    assigned_engineer = row[9]
                    completion_date = row[52]

                    # Drops - location
                    # cable_tag_number = row[70] # --------------> Drop 1
                    rg_6_cable_black_wo_mess = row[71] # --------------> Drop 2
                    rg_6_cable_black_w_mess = row[72] # --------------> Drop 3
                    rg_6_connector = row[73] # --------------> Drop 4
                    ground_block = row[74] # --------------> Drop 5 
                    two_way_splitter = row[75] # --------------> Drop 6
                    ground_rod = row[76] # --------------> Drop 7
                    span_clamp = row[77] # --------------> Drop 8
                    high_pass_filter = row[78] # --------------> Drop 9
                    isolator = row[79] # --------------> Drop 10
                    ground_clamp = row[80] # --------------> Drop 11
                    attenuator_3db = row[81] # --------------> Drop 12
                    attenuator_6db = row[82] # --------------> Drop 13
                    cable_clip = row[83] # --------------> Drop 14
                    cable_tag = row[84] # --------------> Drop 15
                    f_81_connector = row[85] # --------------> Drop 16
                    fiber_optic_apc_connector = row[86] # --------------> Drop 17
                    fiber_optic_patch_cord_bipc_2mtrs = row[87] # --------------> Drop 18
                    fiber_optic_patch_cord_sc_apc_to_sc_apc_3mtrs = row[88] # --------------> Drop 19
                    fiber_optic_patch_cord_sc_apc_to_sc_apc_6mtrs = row[89] # --------------> Drop 20
                    ground_wire = row[90] # --------------> Drop 21
                    p_hook = row[91] # --------------> Drop 22
                    rg_11_cable_w_mess = row[92] # --------------> Drop 23
                    rg_11_connector = row[93] # --------------> Drop 24
                    utp_cable_1_meter = row[94] # --------------> Drop 25

                    # ####################################### <<<<< CONDITIONS >>>> #########################################
                    # ==============================================> TRANSACT INFO 1
                    if callid != "" and callid != "CallID" and row_num > 1:
                        drops_db = self.env['stock.drops.issuance'].search([])
                        if drops_db:
                            for drop in drops_db:
                                # Check if Job Order is already exists
                                if drop.callid == callid:
                                    raise ValidationError('Job Order is already imported at row {} column CallID'.format(row_num))
                                else:
                                    callid_value = callid
                        else:
                            callid_value = callid
                            
                    elif callid == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column CallID'.format(row_num))
                    
                    # ==============================================> TRANSACT INFO 2
                    if task_type_category != "" and task_type_category != "Task Type Category" and row_num > 1:
                        task_type_category_value = task_type_category

                    elif task_type_category == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column Task Type Category'.format(row_num))
                    
                    # ==============================================> TRANSACT INFO 3
                    
                    if assigned_engineer != "" and assigned_engineer != "Assigned Engineer" and row_num > 1:
                        checker = self.env['team.configuration'].search([('team_number', '=', assigned_engineer)])
                        if checker:
                            assigned_engineer_value = checker.team_number
                        else:
                            error = True
                            if error == True:
                                raise ValidationError('Team not found in the database. in row {} column Assigned Engineer'.format(row_num))
                        
                        if str(assigned_engineer_value) in team_names:
                            pass
                        else:
                            team_names.append(str(assigned_engineer_value))

                    elif assigned_engineer == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column Assigned Engineer'.format(row_num))

                    # ==============================================> TRANSACT INFO 4
                    if completion_date != "" and completion_date != "Completion Date" and row_num > 1:
                        completion_date_value = completion_date

                    elif completion_date == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column Completion Date'.format(row_num))

                    # ==============================================> DROP 1
                    if rg_6_cable_black_wo_mess != "" and rg_6_cable_black_wo_mess != "RG-6 CABLE BLACK W/O MESS" and row_num > 1:
                        rg_6_cable_black_wo_mess_value = rg_6_cable_black_wo_mess
                        drop1 = drop1 + long(rg_6_cable_black_wo_mess_value)
                        
                        search_product_id  = self.env['product.product'].search([('product_tmpl_id.clicksolf_code','=','RG-6 CABLE BLACK W/O MESS')], limit=1)
                        ei_validation = self.env['etsi.inventory'].search([('etsi_product_id','=', search_product_id.id),('etsi_team_in','=',assigned_engineer)], limit=1)
                        if search_product_id and ei_validation:
                            if int(ei_validation.etsi_product_quantity) < int(rg_6_cable_black_wo_mess_value):
                                raise UserError("Invalid value clicksolf quantity is higher than the value in team location.\n"+" Product: "+ str(search_product_id.product_tmpl_id.clicksolf_code)+ " Team: "+ str(assigned_engineer_value) + "Row: " + str(row_num))
                        elif rg_6_cable_black_wo_mess_value == "0":
                            pass
                        else:
                            raise UserError("No record found in View all Drops." + " Product: " + 'RG-6 CABLE BLACK W/O MESS\n' + " Team: "+ str(assigned_engineer_value) + " Row: " + str(row_num))
    
                    elif rg_6_cable_black_wo_mess == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column RG-6 CABLE BLACK W/O MESS'.format(row_num))
                    else:
                        # get header value
                        if row_num == 1:
                            drops_names.append(rg_6_cable_black_wo_mess)

                    # ==============================================> DROP 2
                    if rg_6_cable_black_w_mess != "" and rg_6_cable_black_w_mess != "RG-6 CABLE BLACK W/ MESS" and row_num > 1:
                        rg_6_cable_black_w_mess_value = rg_6_cable_black_w_mess
                        drop2 = drop2 + long(rg_6_cable_black_w_mess_value)

                        search_product_id  = self.env['product.product'].search([('product_tmpl_id.clicksolf_code','=','RG-6 CABLE BLACK W/ MESS')], limit=1)
                        ei_validation = self.env['etsi.inventory'].search([('etsi_product_id','=', search_product_id.id),('etsi_team_in','=',assigned_engineer)], limit=1)

                        if search_product_id and ei_validation:
                            if int(ei_validation.etsi_product_quantity) < int(rg_6_cable_black_w_mess_value):
                                raise UserError("Invalid value clicksolf quantity is higher than the value in team location.\n"+" Product: "+ str(search_product_id.product_tmpl_id.clicksolf_code)+ " Team: "+ str(assigned_engineer_value) + "Row: " + str(row_num))
                        elif rg_6_cable_black_w_mess_value == "0":
                            pass
                        else:
                            raise UserError("No record found in View all Drops." + " Product: " + 'RG-6 CABLE BLACK W/ MESS\n' + " Team: "+ str(assigned_engineer_value) + " Row: " + str(row_num))

                    elif rg_6_cable_black_w_mess == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column RG-6 CABLE BLACK W/ MESS'.format(row_num))
                    else:
                        # get header value
                        if row_num == 1:
                            drops_names.append(rg_6_cable_black_w_mess)
                            
                    # ==============================================> DROP 3
                    if rg_6_connector != "" and rg_6_connector != "RG-6 CONNECTOR" and row_num > 1:
                        rg_6_connector_value = rg_6_connector
                        drop3 = drop3 + long(rg_6_connector_value)

                        search_product_id  = self.env['product.product'].search([('product_tmpl_id.clicksolf_code','=','RG-6 CONNECTOR')], limit=1)
                        ei_validation = self.env['etsi.inventory'].search([('etsi_product_id','=', search_product_id.id),('etsi_team_in','=',assigned_engineer)], limit=1)

                        if search_product_id and ei_validation:
                            if int(ei_validation.etsi_product_quantity) < int(rg_6_connector_value):
                                raise UserError("Invalid value clicksolf quantity is higher than the value in team location.\n"+" Product: "+ str(search_product_id.product_tmpl_id.clicksolf_code)+ " Team: "+ str(assigned_engineer_value) + "Row: " + str(row_num))
                        elif rg_6_connector_value == "0":
                            pass
                        else:
                            raise UserError("No record found in View all Drops." + " Product: " + 'RG-6 CONNECTOR\n' + " Team: "+ str(assigned_engineer_value) + " Row: " + str(row_num))

                    elif rg_6_connector == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column RG-6 CONNECTOR'.format(row_num))
                    else:
                        # get header value
                        if row_num == 1:
                            drops_names.append(rg_6_connector)

                    # ==============================================> DROP 4
                    if ground_block != "" and ground_block != "GROUND BLOCK" and row_num > 1:
                        ground_block_value = ground_block
                        drop4 = drop4 + long(ground_block_value)

                        search_product_id  = self.env['product.product'].search([('product_tmpl_id.clicksolf_code','=','GROUND ROD')], limit=1)
                        ei_validation = self.env['etsi.inventory'].search([('etsi_product_id','=', search_product_id.id),('etsi_team_in','=',assigned_engineer)], limit=1)

                        if search_product_id and ei_validation:
                            if int(ei_validation.etsi_product_quantity) < int(ground_rod):
                                raise UserError("Invalid value clicksolf quantity is higher than the value in team location.\n"+" Product: "+ str(search_product_id.product_tmpl_id.clicksolf_code)+ " Team: "+ str(assigned_engineer_value) + "Row: " + str(row_num))
                        elif ground_block_value == "0":
                            pass
                        else:
                            raise UserError("No record found in View all Drops." + " Product: " + 'GROUND ROD\n' + " Team: "+ str(assigned_engineer_value) + " Row: " + str(row_num))

                    elif ground_block == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column GROUND BLOCK'.format(row_num))
                    else:
                        # get header value
                        if row_num == 1:
                            drops_names.append(ground_block)

                    # ==============================================> DROP 5
                    if two_way_splitter != "" and two_way_splitter != "2 WAY SPLITTER" and row_num > 1:
                        two_way_splitter_value = two_way_splitter
                        drop5 = drop5 + long(two_way_splitter_value)

                        search_product_id  = self.env['product.product'].search([('product_tmpl_id.clicksolf_code','=','2 WAY SPLITTER')], limit=1)
                        ei_validation = self.env['etsi.inventory'].search([('etsi_product_id','=', search_product_id.id),('etsi_team_in','=',assigned_engineer)], limit=1)

                        if search_product_id and ei_validation:
                            if int(ei_validation.etsi_product_quantity) < int(two_way_splitter_value):
                                raise UserError("Invalid value clicksolf quantity is higher than the value in team location.\n"+" Product: "+ str(search_product_id.product_tmpl_id.clicksolf_code)+ " Team: "+ str(assigned_engineer_value) + "Row: " + str(row_num))
                        elif two_way_splitter_value == "0":
                            pass
                        else:
                            raise UserError("No record found in View all Drops." + " Product: " + '2 WAY SPLITTER\n' + " Team: "+ str(assigned_engineer_value) + " Row: " + str(row_num))
                           
                    elif two_way_splitter == "":
                        error = True
                        if error == True:   
                            raise ValidationError('Invalid data in row {} column 2 WAY SPLITTER'.format(row_num))
                    else:
                        # get header value
                        if row_num == 1:
                            drops_names.append(two_way_splitter)

                    # ==============================================> DROP 6
                    if ground_rod != "" and ground_rod != "GROUND ROD" and row_num > 1:
                        ground_rod_value = ground_rod
                        drop6 = drop6 + long(ground_rod_value)

                        search_product_id  = self.env['product.product'].search([('product_tmpl_id.clicksolf_code','=','GROUND ROD')], limit=1)
                        ei_validation = self.env['etsi.inventory'].search([('etsi_product_id','=', search_product_id.id),('etsi_team_in','=',assigned_engineer)], limit=1)

                        if search_product_id and ei_validation:
                            if int(ei_validation.etsi_product_quantity) < int(ground_rod_value):
                                raise UserError("Invalid value clicksolf quantity is higher than the value in team location.\n"+" Product: "+ str(search_product_id.product_tmpl_id.clicksolf_code)+ " Team: "+ str(assigned_engineer_value) + "Row: " + str(row_num))
                        elif ground_rod_value == "0":
                            pass
                        else:
                            raise UserError("No record found in View all Drops." + " Product: " + 'GROUND ROD\n' + " Team: "+ str(assigned_engineer_value) + " Row: " + str(row_num))

                    elif ground_rod == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column GROUND ROD'.format(row_num))
                    else:
                        # get header value
                        if row_num == 1:
                            drops_names.append(ground_rod)

                    # ==============================================> DROP 7
                    if span_clamp != "" and span_clamp != "SPAN CLAMP" and row_num > 1:
                        span_clamp_value = span_clamp
                        drop7 = drop7 + long(span_clamp_value)

                        search_product_id  = self.env['product.product'].search([('product_tmpl_id.clicksolf_code','=','SPAN CLAMP')], limit=1)
                        ei_validation = self.env['etsi.inventory'].search([('etsi_product_id','=', search_product_id.id),('etsi_team_in','=',assigned_engineer)], limit=1)

                        if search_product_id and ei_validation:
                            if int(ei_validation.etsi_product_quantity) < int(span_clamp_value):
                                raise UserError("Invalid value clicksolf quantity is higher than the value in team location.\n"+" Product: "+ str(search_product_id.product_tmpl_id.clicksolf_code)+ " Team: "+ str(assigned_engineer_value) + "Row: " + str(row_num))
                        elif span_clamp_value == "0":
                            pass
                        else:
                            raise UserError("No record found in View all Drops." + " Product: " + 'SPAN CLAMP\n' + " Team: "+ str(assigned_engineer_value) + " Row: " + str(row_num))

                    elif span_clamp == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column SPAN CLAMP'.format(row_num))
                    else:
                        # get header value
                        if row_num == 1:
                            drops_names.append(span_clamp)
                           
                    # ==============================================> DROP 8
                    if high_pass_filter != "" and high_pass_filter != "HIGH PASS FILTER" and row_num > 1:
                        high_pass_filter_value = high_pass_filter
                        drop8 = drop8 + long(high_pass_filter_value)

                        search_product_id  = self.env['product.product'].search([('product_tmpl_id.clicksolf_code','=','HIGH PASS FILTER')], limit=1)
                        ei_validation = self.env['etsi.inventory'].search([('etsi_product_id','=', search_product_id.id),('etsi_team_in','=',assigned_engineer)], limit=1)

                        if search_product_id and ei_validation:
                            if int(ei_validation.etsi_product_quantity) < int(high_pass_filter_value):
                                raise UserError("Invalid value clicksolf quantity is higher than the value in team location.\n"+" Product: "+ str(search_product_id.product_tmpl_id.clicksolf_code)+ " Team: "+ str(assigned_engineer_value) + "Row: " + str(row_num))
                        elif high_pass_filter_value == "0":
                            pass
                        else:
                            raise UserError("No record found in View all Drops." + " Product: " + 'HIGH PASS FILTER\n' + " Team: "+ str(assigned_engineer_value) + " Row: " + str(row_num))

                    elif high_pass_filter == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column HIGH PASS FILTER'.format(row_num))
                    else:
                        # get header value
                        if row_num == 1:
                            drops_names.append(high_pass_filter)

                    # ==============================================> DROP 9
                    if isolator != "" and isolator != "ISOLATOR" and row_num > 1:
                        isolator_value = isolator
                        drop9 = drop9 + long(isolator_value)

                        search_product_id  = self.env['product.product'].search([('product_tmpl_id.clicksolf_code','=','ISOLATOR')], limit=1)
                        ei_validation = self.env['etsi.inventory'].search([('etsi_product_id','=', search_product_id.id),('etsi_team_in','=',assigned_engineer)], limit=1)

                        if search_product_id and ei_validation:
                            if int(ei_validation.etsi_product_quantity) < int(isolator_value):
                                raise UserError("Invalid value clicksolf quantity is higher than the value in team location.\n"+" Product: "+ str(search_product_id.product_tmpl_id.clicksolf_code)+ " Team: "+ str(assigned_engineer_value) + "Row: " + str(row_num))
                        elif isolator_value == "0":
                            pass
                        else:
                            raise UserError("No record found in View all Drops." + " Product: " + 'ISOLATOR\n' + " Team: "+ str(assigned_engineer_value) + " Row: " + str(row_num))

                    elif isolator == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column ISOLATOR'.format(row_num))
                    else:
                        # get header value
                        if row_num == 1:
                            drops_names.append(isolator)
                    
                    # ==============================================> DROP 10
                    if ground_clamp != "" and ground_clamp != "GROUND CLAMP" and row_num > 1:
                        ground_clamp_value = ground_clamp
                        drop10 = drop10 + long(ground_clamp_value)

                        search_product_id  = self.env['product.product'].search([('product_tmpl_id.clicksolf_code','=','GROUND CLAMP')], limit=1)
                        ei_validation = self.env['etsi.inventory'].search([('etsi_product_id','=', search_product_id.id),('etsi_team_in','=',assigned_engineer)], limit=1)

                        if search_product_id and ei_validation:
                            if int(ei_validation.etsi_product_quantity) < int(ground_clamp_value):
                                raise UserError("Invalid value clicksolf quantity is higher than the value in team location.\n"+" Product: "+ str(search_product_id.product_tmpl_id.clicksolf_code)+ " Team: "+ str(assigned_engineer_value) + "Row: " + str(row_num))
                        elif ground_clamp_value == "0":
                            pass
                        else:
                            raise UserError("No record found in View all Drops." + " Product: " + 'GROUND CLAMP\n' + " Team: "+ str(assigned_engineer_value) + " Row: " + str(row_num))

                    elif ground_clamp == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column GROUND CLAMP'.format(row_num))
                    else:
                        # get header value
                        if row_num == 1:
                            drops_names.append(ground_clamp)
                    
                    # ==============================================> DROP 11
                    if attenuator_3db != "" and attenuator_3db != "ATTENUATOR 3dB" and row_num > 1:
                        attenuator_3db_value = attenuator_3db
                        drop11 = drop11 + long(attenuator_3db_value)

                        search_product_id  = self.env['product.product'].search([('product_tmpl_id.clicksolf_code','=','ATTENUATOR 3dB')], limit=1)
                        ei_validation = self.env['etsi.inventory'].search([('etsi_product_id','=', search_product_id.id),('etsi_team_in','=',assigned_engineer)], limit=1)

                        if search_product_id and ei_validation:
                            if int(ei_validation.etsi_product_quantity) < int(attenuator_3db_value):
                                raise UserError("Invalid value clicksolf quantity is higher than the value in team location.\n"+" Product: "+ str(search_product_id.product_tmpl_id.clicksolf_code)+ " Team: "+ str(assigned_engineer_value) + "Row: " + str(row_num))
                        elif attenuator_3db_value == "0":
                            pass
                        else:
                            raise UserError("No record found in View all Drops." + " Product: " + 'ATTENUATOR 3dB\n' + " Team: "+ str(assigned_engineer_value) + " Row: " + str(row_num))

                    elif attenuator_3db == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column ATTENUATOR 3dB'.format(row_num))
                    else:
                        # get header value
                        if row_num == 1:
                            drops_names.append(attenuator_3db)
                    
                    # ==============================================> DROP 12
                    if attenuator_6db != "" and attenuator_6db != "ATTENUATOR 6dB" and row_num > 1:
                        attenuator_6db_value = attenuator_6db
                        drop12 = drop12 + long(attenuator_6db_value)

                        search_product_id  = self.env['product.product'].search([('product_tmpl_id.clicksolf_code','=','ATTENUATOR 6dB')], limit=1)
                        ei_validation = self.env['etsi.inventory'].search([('etsi_product_id','=', search_product_id.id),('etsi_team_in','=',assigned_engineer)], limit=1)

                        if search_product_id and ei_validation:
                            if int(ei_validation.etsi_product_quantity) < int(attenuator_6db_value):
                                raise UserError("Invalid value clicksolf quantity is higher than the value in team location.\n"+" Product: "+ str(search_product_id.product_tmpl_id.clicksolf_code)+ " Team: "+ str(assigned_engineer_value) + "Row: " + str(row_num))
                        elif attenuator_6db_value == "0":
                            pass
                        else:
                            raise UserError("No record found in View all Drops." + " Product: " + 'ATTENUATOR 6dB\n' + " Team: "+ str(assigned_engineer_value) + " Row: " + str(row_num))

                    elif attenuator_6db == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column ATTENUATOR 6dB'.format(row_num))
                    else:
                        # get header value
                        if row_num == 1:
                            drops_names.append(attenuator_6db)
                    
                    # ==============================================> DROP 13
                    if cable_clip != "" and cable_clip != "CABLE CLIP" and row_num > 1:
                        cable_clip_value = cable_clip
                        drop13 = drop13 + long(cable_clip_value)

                        search_product_id  = self.env['product.product'].search([('product_tmpl_id.clicksolf_code','=','CABLE CLIP')], limit=1)
                        ei_validation = self.env['etsi.inventory'].search([('etsi_product_id','=', search_product_id.id),('etsi_team_in','=',assigned_engineer)], limit=1)

                        if search_product_id and ei_validation:
                            if int(ei_validation.etsi_product_quantity) < int(cable_clip_value):
                                raise UserError("Invalid value clicksolf quantity is higher than the value in team location.\n"+" Product: "+ str(search_product_id.product_tmpl_id.clicksolf_code)+ " Team: "+ str(assigned_engineer_value) + "Row: " + str(row_num))
                        elif cable_clip_value == "0":
                            pass
                        else:
                            raise UserError("No record found in View all Drops." + " Product: " + 'CABLE CLIP\n' + " Team: "+ str(assigned_engineer_value) + " Row: " + str(row_num))

                    elif cable_clip == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column CABLE CLIP'.format(row_num))
                    else:
                        # get header value
                        if row_num == 1:
                            drops_names.append(cable_clip)

                    # ==============================================> DROP 14
                    if cable_tag != "" and cable_tag != "CABLE TAG" and row_num > 1:
                        cable_tag_value = cable_tag
                        drop14 = drop14 + long(cable_tag_value)

                        search_product_id  = self.env['product.product'].search([('product_tmpl_id.clicksolf_code','=','CABLE TAG')], limit=1)
                        ei_validation = self.env['etsi.inventory'].search([('etsi_product_id','=', search_product_id.id),('etsi_team_in','=',assigned_engineer)], limit=1)

                        if search_product_id and ei_validation:
                            if int(ei_validation.etsi_product_quantity) < int(cable_tag_value):
                                raise UserError("Invalid value clicksolf quantity is higher than the value in team location.\n"+" Product: "+ str(search_product_id.product_tmpl_id.clicksolf_code)+ " Team: "+ str(assigned_engineer_value) + "Row: " + str(row_num))
                        elif cable_tag_value == "0":
                            pass
                        else:
                            raise UserError("No record found in View all Drops." + " Product: " + 'CABLE TAG\n' + " Team: "+ str(assigned_engineer_value) + " Row: " + str(row_num))

                    elif cable_tag == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column CABLE TAG'.format(row_num))
                    else:
                        # get header value
                        if row_num == 1:
                            drops_names.append(cable_tag)
                    
                    # ==============================================> DROP 15
                    if f_81_connector != "" and f_81_connector != "F-81 CONNECTOR" and row_num > 1:
                        f_81_connector_value = f_81_connector
                        drop15 = drop15 + long(f_81_connector_value)

                        search_product_id  = self.env['product.product'].search([('product_tmpl_id.clicksolf_code','=','F-81 CONNECTOR')], limit=1)
                        ei_validation = self.env['etsi.inventory'].search([('etsi_product_id','=', search_product_id.id),('etsi_team_in','=',assigned_engineer)], limit=1)

                        if search_product_id and ei_validation:
                            if int(ei_validation.etsi_product_quantity) < int(f_81_connector_value):
                                raise UserError("Invalid value clicksolf quantity is higher than the value in team location.\n"+" Product: "+ str(search_product_id.product_tmpl_id.clicksolf_code)+ " Team: "+ str(assigned_engineer_value) + "Row: " + str(row_num))
                        elif f_81_connector_value == "0":
                            pass
                        else:
                            raise UserError("No record found in View all Drops." + " Product: " + 'F-81 CONNECTOR\n' + " Team: "+ str(assigned_engineer_value) + " Row: " + str(row_num))

                    elif f_81_connector == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column F-81 CONNECTOR'.format(row_num))
                    else:
                        # get header value
                        if row_num == 1:
                            drops_names.append(f_81_connector)

                    # ==============================================> DROP 16
                    if fiber_optic_apc_connector != "" and fiber_optic_apc_connector != "FIBER OPTIC APC CONNECTOR" and row_num > 1:
                        fiber_optic_apc_connector_value = fiber_optic_apc_connector
                        drop16 = drop16 + long(fiber_optic_apc_connector_value)

                        search_product_id  = self.env['product.product'].search([('product_tmpl_id.clicksolf_code','=','FIBER OPTIC APC CONNECTOR')], limit=1)
                        ei_validation = self.env['etsi.inventory'].search([('etsi_product_id','=', search_product_id.id),('etsi_team_in','=',assigned_engineer)], limit=1)

                        if search_product_id and ei_validation:
                            if int(ei_validation.etsi_product_quantity) < int(fiber_optic_apc_connector_value):
                                raise UserError("Invalid value clicksolf quantity is higher than the value in team location.\n"+" Product: "+ str(search_product_id.product_tmpl_id.clicksolf_code)+ " Team: "+ str(assigned_engineer_value) + "Row: " + str(row_num))
                        elif fiber_optic_apc_connector_value == "0":
                            pass
                        else:
                            raise UserError("No record found in View all Drops." + " Product: " + 'FIBER OPTIC APC CONNECTOR\n' + " Team: "+ str(assigned_engineer_value) + " Row: " + str(row_num))

                    elif fiber_optic_apc_connector == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column FIBER OPTIC APC CONNECTOR'.format(row_num))
                    else:
                        # get header value
                        if row_num == 1:
                            drops_names.append(fiber_optic_apc_connector)
                    
                    # ==============================================> DROP 17
                    if fiber_optic_patch_cord_bipc_2mtrs != "" and fiber_optic_patch_cord_bipc_2mtrs != "FIBER OPTIC PATCH CORD BIPC 2mtrs" and row_num > 1:
                        fiber_optic_patch_cord_bipc_2mtrs_value = fiber_optic_patch_cord_bipc_2mtrs
                        drop17 = drop17 + long(fiber_optic_patch_cord_bipc_2mtrs_value)

                        search_product_id  = self.env['product.product'].search([('product_tmpl_id.clicksolf_code','=','FIBER OPTIC PATCH CORD BIPC 2mtrs')], limit=1)
                        ei_validation = self.env['etsi.inventory'].search([('etsi_product_id','=', search_product_id.id),('etsi_team_in','=',assigned_engineer)], limit=1)

                        if search_product_id and ei_validation:
                            if int(ei_validation.etsi_product_quantity) < int(fiber_optic_patch_cord_bipc_2mtrs_value):
                                raise UserError("Invalid value clicksolf quantity is higher than the value in team location.\n"+" Product: "+ str(search_product_id.product_tmpl_id.clicksolf_code)+ " Team: "+ str(assigned_engineer_value) + "Row: " + str(row_num))
                        elif fiber_optic_patch_cord_bipc_2mtrs_value == "0":
                            pass
                        else:
                            raise UserError("No record found in View all Drops." + " Product: " + 'FIBER OPTIC PATCH CORD BIPC 2mtrs\n' + " Team: "+ str(assigned_engineer_value) + " Row: " + str(row_num))

                    elif fiber_optic_patch_cord_bipc_2mtrs == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column FIBER OPTIC PATCH CORD BIPC 2mtrs'.format(row_num))
                    else:
                        # get header value
                        if row_num == 1:
                            drops_names.append(fiber_optic_patch_cord_bipc_2mtrs)

                    # ==============================================> DROP 18
                    if fiber_optic_patch_cord_sc_apc_to_sc_apc_3mtrs != "" and fiber_optic_patch_cord_sc_apc_to_sc_apc_3mtrs != "FIBER OPTIC PATCH CORD SC/APC to SC/APC 3mtrs" and row_num > 1:
                        fiber_optic_patch_cord_sc_apc_to_sc_apc_3mtrs_value = fiber_optic_patch_cord_sc_apc_to_sc_apc_3mtrs
                        drop18 = drop18 + long(fiber_optic_patch_cord_sc_apc_to_sc_apc_3mtrs_value)

                        search_product_id  = self.env['product.product'].search([('product_tmpl_id.clicksolf_code','=','FIBER OPTIC PATCH CORD SC/APC to SC/APC 3mtrs')], limit=1)
                        ei_validation = self.env['etsi.inventory'].search([('etsi_product_id','=', search_product_id.id),('etsi_team_in','=',assigned_engineer)], limit=1)

                        if search_product_id and ei_validation:
                            if int(ei_validation.etsi_product_quantity) < int(fiber_optic_patch_cord_sc_apc_to_sc_apc_3mtrs_value):
                                raise UserError("Invalid value clicksolf quantity is higher than the value in team location.\n"+" Product: "+ str(search_product_id.product_tmpl_id.clicksolf_code)+ " Team: "+ str(assigned_engineer_value) + "Row: " + str(row_num))
                        elif fiber_optic_patch_cord_sc_apc_to_sc_apc_3mtrs_value == "0":
                            pass
                        else:
                            raise UserError("No record found in View all Drops." + " Product: " + 'FIBER OPTIC PATCH CORD SC/APC to SC/APC 3mtrs\n' + " Team: "+ str(assigned_engineer_value) + " Row: " + str(row_num))
                            
                    elif fiber_optic_patch_cord_sc_apc_to_sc_apc_3mtrs == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column FIBER OPTIC PATCH CORD SC/APC to SC/APC 3mtrs'.format(row_num))
                    else:
                        # get header value
                        if row_num == 1:
                            drops_names.append(fiber_optic_patch_cord_sc_apc_to_sc_apc_3mtrs)

                    # ==============================================> DROP 19
                    if fiber_optic_patch_cord_sc_apc_to_sc_apc_6mtrs != "" and fiber_optic_patch_cord_sc_apc_to_sc_apc_6mtrs != "FIBER OPTIC PATCH CORD SC/APC to SC/APC 6mtrs" and row_num > 1:
                        fiber_optic_patch_cord_sc_apc_to_sc_apc_6mtrs_value = fiber_optic_patch_cord_sc_apc_to_sc_apc_6mtrs
                        drop19 = drop19 + long(fiber_optic_patch_cord_sc_apc_to_sc_apc_6mtrs_value)

                        search_product_id  = self.env['product.product'].search([('product_tmpl_id.clicksolf_code','=','FIBER OPTIC PATCH CORD SC/APC to SC/APC 6mtrs')], limit=1)
                        ei_validation = self.env['etsi.inventory'].search([('etsi_product_id','=', search_product_id.id),('etsi_team_in','=',assigned_engineer)], limit=1)

                        if search_product_id and ei_validation:
                            if int(ei_validation.etsi_product_quantity) < int(fiber_optic_patch_cord_sc_apc_to_sc_apc_6mtrs_value):
                                raise UserError("Invalid value clicksolf quantity is higher than the value in team location.\n"+" Product: "+ str(search_product_id.product_tmpl_id.clicksolf_code)+ " Team: "+ str(assigned_engineer_value) + "Row: " + str(row_num))
                        elif fiber_optic_patch_cord_sc_apc_to_sc_apc_6mtrs_value == "0":
                            pass
                        else:
                            raise UserError("No record found in View all Drops." + " Product: " + 'FIBER OPTIC PATCH CORD SC/APC to SC/APC 6mtrs\n' + " Team: "+ str(assigned_engineer_value) + " Row: " + str(row_num))

                    elif fiber_optic_patch_cord_sc_apc_to_sc_apc_6mtrs == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column FIBER OPTIC PATCH CORD SC/APC to SC/APC 6mtrs'.format(row_num))
                    else:
                        # get header value
                        if row_num == 1:
                            drops_names.append(fiber_optic_patch_cord_sc_apc_to_sc_apc_6mtrs)

                    # ==============================================> DROP 20
                    if ground_wire != "" and ground_wire != "GROUND WIRE" and row_num > 1:
                        ground_wire_value = ground_wire
                        drop20 = drop20 + long(ground_wire_value)

                        search_product_id  = self.env['product.product'].search([('product_tmpl_id.clicksolf_code','=','GROUND WIRE')], limit=1)
                        ei_validation = self.env['etsi.inventory'].search([('etsi_product_id','=', search_product_id.id),('etsi_team_in','=',assigned_engineer)], limit=1)

                        if search_product_id and ei_validation:
                            if int(ei_validation.etsi_product_quantity) < int(ground_wire_value):
                                raise UserError("Invalid value clicksolf quantity is higher than the value in team location.\n"+" Product: "+ str(search_product_id.product_tmpl_id.clicksolf_code)+ " Team: "+ str(assigned_engineer_value) + "Row: " + str(row_num))
                        elif ground_wire_value == "0":
                            pass
                        else:
                            raise UserError("No record found in View all Drops." + " Product: " + 'GROUND WIRE\n' + " Team: "+ str(assigned_engineer_value) + " Row: " + str(row_num))
                            
                    elif ground_wire == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column GROUND WIRE'.format(row_num))
                    else:
                        # get header value
                        if row_num == 1:
                            drops_names.append(ground_wire)
                    
                    # ==============================================> DROP 21
                    if p_hook != "" and p_hook != "P-HOOK" and row_num > 1:
                        p_hook_value = p_hook
                        drop21 = drop21 + long(p_hook_value)

                        search_product_id  = self.env['product.product'].search([('product_tmpl_id.clicksolf_code','=','P-HOOK')], limit=1)
                        ei_validation = self.env['etsi.inventory'].search([('etsi_product_id','=', search_product_id.id),('etsi_team_in','=',assigned_engineer)], limit=1)

                        if search_product_id and ei_validation:
                            if int(ei_validation.etsi_product_quantity) < int(p_hook_value):
                                raise UserError("Invalid value clicksolf quantity is higher than the value in team location.\n"+" Product: "+ str(search_product_id.product_tmpl_id.clicksolf_code)+ " Team: "+ str(assigned_engineer_value) + "Row: " + str(row_num))
                        elif p_hook_value == "0":
                            pass
                        else:
                            raise UserError("No record found in View all Drops." + " Product: " + 'P-HOOK\n' + " Team: "+ str(assigned_engineer_value) + " Row: " + str(row_num))

                    elif p_hook == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column P-HOOK'.format(row_num))
                    else:
                        # get header value
                        if row_num == 1:
                            drops_names.append(p_hook)
                    
                    # ==============================================> DROP 22
                    if rg_11_cable_w_mess != "" and rg_11_cable_w_mess != "RG-11 CABLE W/ MESS" and row_num > 1:
                        rg_11_cable_w_mess_value = rg_11_cable_w_mess
                        drop22 = drop22 + long(rg_11_cable_w_mess_value)

                        search_product_id  = self.env['product.product'].search([('product_tmpl_id.clicksolf_code','=','RG-11 CABLE W/ MESS')], limit=1)
                        ei_validation = self.env['etsi.inventory'].search([('etsi_product_id','=', search_product_id.id),('etsi_team_in','=',assigned_engineer)], limit=1)

                        if search_product_id and ei_validation:
                            if int(ei_validation.etsi_product_quantity) < int(rg_11_cable_w_mess_value):
                                raise UserError("Invalid value clicksolf quantity is higher than the value in team location.\n"+" Product: "+ str(search_product_id.product_tmpl_id.clicksolf_code)+ " Team: "+ str(assigned_engineer_value) + "Row: " + str(row_num))
                        elif rg_11_cable_w_mess_value == "0":
                            pass
                        else:
                            raise UserError("No record found in View all Drops." + " Product: " + 'RG-11 CABLE W/ MESS\n' + " Team: "+ str(assigned_engineer_value) + " Row: " + str(row_num))

                    elif rg_11_cable_w_mess == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column RG-11 CABLE W/ MESS'.format(row_num))
                    else:
                        # get header value
                        if row_num == 1:
                            drops_names.append(rg_11_cable_w_mess)

                    # ==============================================> DROP 23
                    if rg_11_connector != "" and rg_11_connector != "RG-11 CONNECTOR" and row_num > 1:
                        rg_11_connector_value = rg_11_connector
                        drop23 = drop23 + long(rg_11_connector_value)

                        search_product_id  = self.env['product.product'].search([('product_tmpl_id.clicksolf_code','=','RG-11 CONNECTOR')], limit=1)
                        ei_validation = self.env['etsi.inventory'].search([('etsi_product_id','=', search_product_id.id),('etsi_team_in','=',assigned_engineer)], limit=1)

                        if search_product_id and ei_validation:
                            if int(ei_validation.etsi_product_quantity) < int(rg_11_connector_value):
                                raise UserError("Invalid value clicksolf quantity is higher than the value in team location.\n"+" Product: "+ str(search_product_id.product_tmpl_id.clicksolf_code)+ " Team: "+ str(assigned_engineer_value) + "Row: " + str(row_num))
                        elif rg_11_connector_value == "0":
                            pass
                        else:
                            raise UserError("No record found in View all Drops." + " Product: " + 'RG-11 CONNECTOR\n' + " Team: "+ str(assigned_engineer_value) + " Row: " + str(row_num))
                            
                    elif rg_11_connector == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column RG-11 CONNECTOR'.format(row_num))
                    else:
                        # get header value
                        if row_num == 1:
                            drops_names.append(rg_11_connector)
                    
                    # ==============================================> DROP 24
                    if utp_cable_1_meter != "" and utp_cable_1_meter != "UTP CABLE 1 meter" and row_num > 1:
                        utp_cable_1_meter_value = utp_cable_1_meter
                        drop24 = drop24 + long(utp_cable_1_meter_value)

                        search_product_id  = self.env['product.product'].search([('product_tmpl_id.clicksolf_code','=','UTP CABLE 1 meter')], limit=1)
                        ei_validation = self.env['etsi.inventory'].search([('etsi_product_id','=', search_product_id.id),('etsi_team_in','=',assigned_engineer)], limit=1)

                        if search_product_id and ei_validation:
                            if int(ei_validation.etsi_product_quantity) < int(utp_cable_1_meter_value):
                                raise UserError("Invalid value clicksolf quantity is higher than the value in team location.\n"+" Product: "+ str(search_product_id.product_tmpl_id.clicksolf_code)+ " Team: "+ str(assigned_engineer_value) + "Row: " + str(row_num))
                        elif utp_cable_1_meter_value == "0":
                            pass
                        else:
                            raise UserError("No record found in View all Drops." + " Product: " + 'UTP CABLE 1 meter\n' + " Team: "+ str(assigned_engineer_value) + " Row: " + str(row_num))

                    elif utp_cable_1_meter == "":
                        error = True
                        if error == True:
                            raise ValidationError('Invalid data in row {} column UTP CABLE 1 meter'.format(row_num))
                    else:
                        # get header value
                        if row_num == 1:
                            drops_names.append(utp_cable_1_meter)

                    if row_num == 1:
                        for record in drops_names:
                            checker = self.env['product.template'].search([('clicksolf_code', '=', record)])

                            if not checker:
                                raise ValidationError("Product " + record + " not found in product database!")

                    # Insert data into database
                    if row_num > 1: 
                        data_dict ={
                            # Transaction Info - Values
                            'callid_value':callid_value,
                            'task_type_category_value':task_type_category_value,
                            'assigned_engineer_value':assigned_engineer_value,
                            'completion_date_value':completion_date_value,

                            # Drops - Values
                            'rg_6_cable_black_wo_mess_value':str(rg_6_cable_black_wo_mess_value).replace(',', '').replace(' ', ''),
                            'rg_6_cable_black_w_mess_value':str(rg_6_cable_black_w_mess_value).replace(',', '').replace(' ', ''),
                            'rg_6_connector_value':str(rg_6_connector_value).replace(',', '').replace(' ', ''),
                            'ground_block_value':str(ground_block_value).replace(',', '').replace(' ', ''),
                            'two_way_splitter_value':str(two_way_splitter_value).replace(',', '').replace(' ', '') ,
                            'ground_rod_value':str(ground_rod_value).replace(',', '').replace(' ', ''),
                            'span_clamp_value':str(span_clamp_value).replace(',', '').replace(' ', ''),
                            'high_pass_filter_value':str(high_pass_filter_value).replace(',', '').replace(' ', ''),
                            'isolator_value':str(isolator_value).replace(',', '').replace(' ', ''),
                            'ground_clamp_value':str(ground_clamp_value).replace(',', '').replace(' ', '') ,
                            'attenuator_3db_value':str(attenuator_3db_value).replace(',', '').replace(' ', ''),
                            'attenuator_6db_value':str(attenuator_6db_value).replace(',', '').replace(' ', ''),
                            'cable_clip_value':str(cable_clip_value).replace(',', '').replace(' ', ''),
                            'cable_tag_value':str(cable_tag_value).replace(',', '').replace(' ', ''),
                            'f_81_connector_value':str(f_81_connector_value).replace(',', '').replace(' ', ''),
                            'fiber_optic_apc_connector_value':str(fiber_optic_apc_connector_value).replace(',', '').replace(' ', ''),
                            'fiber_optic_patch_cord_bipc_2mtrs_value':str(fiber_optic_patch_cord_bipc_2mtrs_value).replace(',', '').replace(' ', ''),
                            'fiber_optic_patch_cord_sc_apc_to_sc_apc_3mtrs_value':str(fiber_optic_patch_cord_sc_apc_to_sc_apc_3mtrs_value).replace(',', '').replace(' ', ''),
                            'fiber_optic_patch_cord_sc_apc_to_sc_apc_6mtrs_value':str(fiber_optic_patch_cord_sc_apc_to_sc_apc_6mtrs_value).replace(',', '').replace(' ', ''),
                            'ground_wire_value':str(ground_wire_value).replace(',', '').replace(' ', '') ,
                            'p_hook_value':str(p_hook_value).replace(',', '').replace(' ', ''),
                            'rg_11_cable_w_mess_value':str(rg_11_cable_w_mess_value).replace(',', '').replace(' ', ''),
                            'rg_11_connector_value':str(rg_11_connector_value).replace(',', '').replace(' ', ''),
                            'utp_cable_1_meter_value':str(utp_cable_1_meter_value).replace(',', '').replace(' ', ''),
                        }

                        data_list.append(data_dict)
                        data_dict={}

                for rec in team_names: 
                    for record in drops_names:  
                        search_product_id  = self.env['product.product'].search([('product_tmpl_id.clicksolf_code','=',record)])
                        ei_validation = self.env['etsi.inventory'].search([('etsi_product_id','=', search_product_id.id),('etsi_team_in','=',rec)])

                        if search_product_id and ei_validation:
                            if int(ei_validation.etsi_product_quantity) < drop1 and drop1 != 0:
                                raise ValidationError('Invalid clicksoft quantity is greater than the quantity in view all drops.\n' + "Product: " + str(drops_names[0]) +" Team: "+rec) 
                            elif int(ei_validation.etsi_product_quantity) < drop2:
                                raise ValidationError('Invalid clicksoft quantity is greater than the quantity in view all drops.\n' + "Product: " + str(drops_names[1]) +" Team: "+rec)
                            elif int(ei_validation.etsi_product_quantity) < drop3:
                                raise ValidationError('Invalid clicksoft quantity is greater than the quantity in view all drops.\n' + "Product: " + str(drops_names[2]) +" Team: "+rec)
                            elif int(ei_validation.etsi_product_quantity) < drop4:
                                raise ValidationError('Invalid clicksoft quantity is greater than the quantity in view all drops.\n' + "Product: " + str(drops_names[3]) +" Team: "+rec)
                            elif int(ei_validation.etsi_product_quantity) < drop5:
                                raise ValidationError('Invalid clicksoft quantity is greater than the quantity in view all drops.\n' + "Product: " + str(drops_names[4]) +" Team: "+rec)
                            elif int(ei_validation.etsi_product_quantity) < drop6:
                                raise ValidationError('Invalid clicksoft quantity is greater than the quantity in view all drops.\n' + "Product: " + str(drops_names[5]) +" Team: "+rec)
                            elif int(ei_validation.etsi_product_quantity) < drop7:
                                raise ValidationError('Invalid clicksoft quantity is greater than the quantity in view all drops.\n' + "Product: " + str(drops_names[6]) +" Team: "+rec)
                            elif int(ei_validation.etsi_product_quantity) < drop8:
                                raise ValidationError('Invalid clicksoft quantity is greater than the quantity in view all drops.\n' + "Product: " + str(drops_names[7]) +" Team: "+rec)
                            elif int(ei_validation.etsi_product_quantity) < drop9:
                                raise ValidationError('Invalid clicksoft quantity is greater than the quantity in view all drops.\n' + "Product: " + str(drops_names[8]) +" Team: "+rec)
                            elif int(ei_validation.etsi_product_quantity) < drop10:
                                raise ValidationError('Invalid clicksoft quantity is greater than the quantity in view all drops.\n' + "Product: " + str(drops_names[9]) +" Team: "+rec)
                            elif int(ei_validation.etsi_product_quantity) < drop11:
                                raise ValidationError('Invalid clicksoft quantity is greater than the quantity in view all drops.\n' + "Product: " + str(drops_names[10]) +" Team: "+rec)
                            elif int(ei_validation.etsi_product_quantity) < drop12:
                                raise ValidationError('Invalid clicksoft quantity is greater than the quantity in view all drops.\n' + "Product: " + str(drops_names[11]) +" Team: "+rec)
                            elif int(ei_validation.etsi_product_quantity) < drop13:
                                raise ValidationError('Invalid clicksoft quantity is greater than the quantity in view all drops.\n' + "Product: " + str(drops_names[12]) +" Team: "+rec)
                            elif int(ei_validation.etsi_product_quantity) < drop14:
                                raise ValidationError('Invalid clicksoft quantity is greater than the quantity in view all drops.\n' + "Product: " + str(drops_names[13]) +" Team: "+rec)
                            elif int(ei_validation.etsi_product_quantity) < drop15:
                                raise ValidationError('Invalid clicksoft quantity is greater than the quantity in view all drops.\n' + "Product: " + str(drops_names[14]) +" Team: "+rec)
                            elif int(ei_validation.etsi_product_quantity) < drop16:
                                raise ValidationError('Invalid clicksoft quantity is greater than the quantity in view all drops.\n' + "Product: " + str(drops_names[15]) +" Team: "+rec)
                            elif int(ei_validation.etsi_product_quantity) < drop17:
                                raise ValidationError('Invalid clicksoft quantity is greater than the quantity in view all drops.\n' + "Product: " + str(drops_names[16]) +" Team: "+rec)
                            elif int(ei_validation.etsi_product_quantity) < drop18:
                                raise ValidationError('Invalid clicksoft quantity is greater than the quantity in view all drops.\n' + "Product: " + str(drops_names[17]) +" Team: "+rec)

                            elif int(ei_validation.etsi_product_quantity) < drop19:
                                raise ValidationError('Invalid clicksoft quantity is greater than the quantity in view all drops.\n' + "Product: " + str(drops_names[18]) +" Team: "+rec)
                            elif int(ei_validation.etsi_product_quantity) < drop20:
                                raise ValidationError('Invalid clicksoft quantity is greater than the quantity in view all drops.\n' + "Product: " + str(drops_names[19]) +" Team: "+rec)
                            elif int(ei_validation.etsi_product_quantity) < drop21:
                                raise ValidationError('Invalid clicksoft quantity is greater than the quantity in view all drops.\n' + "Product: " + str(drops_names[20]) +" Team: "+rec)
                            elif int(ei_validation.etsi_product_quantity) < drop22:
                                raise ValidationError('Invalid clicksoft quantity is greater than the quantity in view all drops.\n' + "Product: " + str(drops_names[21]) +" Team: "+rec)

                            elif int(ei_validation.etsi_product_quantity) < drop23:
                                raise ValidationError('Invalid clicksoft quantity is greater than the quantity in view all drops.\n' + "Product: " + str(drops_names[22]) +" Team: "+rec)
                            elif int(ei_validation.etsi_product_quantity) < drop24:
                                raise ValidationError('Invalid clicksoft quantity is greater than the quantity in view all drops.\n' + "Product: " + str(drops_names[23]) +" Team: "+ rec)
                            else:
                                pass  

                if error == False:
                    self.import_batch ="New"
                    vals = {'import_batch': 'New'}
                    record = self.env['stock.drops.import'].browse(self.ids)
                    record.write(vals)
                    new_record = record.create(vals)
                    self.final_batch = new_record.import_batch

                for line in data_list:
                    checker = self.env['team.configuration'].search([('team_number', '=', line['assigned_engineer_value'])])
                    team_id = checker.id
                    count = 0
                    
                    if int(float(line['rg_6_cable_black_wo_mess_value'])) > 0:
                        count +=1
                    if int(float(line['rg_6_cable_black_w_mess_value'])) > 0:
                        count +=1
                    if int(float(line['rg_6_connector_value'])) > 0:
                        count +=1
                    if int(float(line['ground_block_value'])) > 0:
                        count +=1
                    if int(float(line['two_way_splitter_value'])) > 0:
                        count +=1
                    if int(float(line['ground_rod_value'])) > 0:
                        count +=1
                    if int(float(line['span_clamp_value'])) > 0:
                        count +=1
                    if int(float(line['high_pass_filter_value'])) > 0:
                        count +=1
                    if int(float(line['isolator_value'])) > 0:
                        count +=1
                    if int(float(line['ground_clamp_value'])) > 0:
                        count +=1
                    if int(float(line['attenuator_3db_value'])) > 0:
                        count +=1
                    if int(float(line['attenuator_6db_value'])) > 0:
                        count +=1
                    if int(float(line['cable_clip_value'])) > 0:
                        count +=1
                    if int(float(line['cable_tag_value'])) > 0:
                        count +=1
                    if int(float(line['f_81_connector_value'])) > 0:
                        count +=1
                    if int(float(line['fiber_optic_apc_connector_value'])) > 0:
                        count +=1
                    if int(float(line['fiber_optic_patch_cord_bipc_2mtrs_value'])) > 0:
                        count +=1
                    if int(float(line['fiber_optic_patch_cord_sc_apc_to_sc_apc_3mtrs_value'])) > 0:
                        count +=1
                    if int(float(line['fiber_optic_patch_cord_sc_apc_to_sc_apc_6mtrs_value'])) > 0:
                        count +=1
                    if int(float(line['ground_wire_value'])) > 0:
                        count +=1
                    if int(float(line['p_hook_value'])) > 0:
                        count +=1
                    if int(float(line['rg_11_cable_w_mess_value'])) > 0:
                        count +=1
                    if int(float(line['rg_11_connector_value'])) > 0:
                        count +=1
                    if int(float(line['utp_cable_1_meter_value'])) > 0:
                        count +=1

                    self.env['stock.drops.issuance'].create({
                        # Transaction Info - Values
                        'import_batch':self.final_batch,
                        'callid':line['callid_value'],
                        'task_type_category':line['task_type_category_value'],
                        'assigned_engineer':team_id,
                        'completion_date':line['completion_date_value'],
                        'employee_name':self.employee_name.id,
                        'date_time':self.date_time,
                        'stats': "draft",
                        'counter_drops':count,

                        # Drops - Values
                        'rg_6_cable_black_wo_mess_qty':int(float(line['rg_6_cable_black_wo_mess_value'])),
                        'rg_6_cable_black_w_mess_qty':int(float(line['rg_6_cable_black_w_mess_value'])),
                        'rg_6_connector_qty':int(float(line['rg_6_connector_value'])),
                        'ground_block_qty':int(float(line['ground_block_value'])),
                        'two_way_splitter_qty':int(float(line['two_way_splitter_value'])) ,

                        'ground_rod_qty':int(float(line['ground_rod_value'])),
                        'span_clamp_qty':int(float(line['span_clamp_value'])),
                        'high_pass_filter_qty':int(float(line['high_pass_filter_value'])),
                        'isolator_qty':int(float(line['isolator_value'])),
                        'ground_clamp_qty':int(float(line['ground_clamp_value'])) ,

                        'attenuator_3db_qty':int(float(line['attenuator_3db_value'])),
                        'attenuator_6db_qty':int(float(line['attenuator_6db_value'])),
                        'cable_clip_qty':int(float(line['cable_clip_value'])),
                        'cable_tag_qty':int(float(line['cable_tag_value'])),
                        'f_81_connector_qty':int(float(line['f_81_connector_value'])) ,

                        'fiber_optic_apc_connector_qty':int(float(line['fiber_optic_apc_connector_value'])),
                        'fiber_optic_patch_cord_bipc_2mtrs_qty':int(float(line['fiber_optic_patch_cord_bipc_2mtrs_value'])),
                        'fiber_optic_patch_cord_sc_apc_to_sc_apc_3mtrs_qty':int(float(line['fiber_optic_patch_cord_sc_apc_to_sc_apc_3mtrs_value'])),
                        'fiber_optic_patch_cord_sc_apc_to_sc_apc_6mtrs_qty':int(float(line['fiber_optic_patch_cord_sc_apc_to_sc_apc_6mtrs_value'])),
                        'ground_wire_qty':int(line['ground_wire_value']) ,

                        'p_hook_qty':int(line['p_hook_value']),
                        'rg_11_cable_w_mess_qty':int(line['rg_11_cable_w_mess_value']),
                        'rg_11_connector_qty':int(line['rg_11_connector_value']),
                        'utp_cable_1_meter_qty':int(line['utp_cable_1_meter_value']),
                    })

    @api.model
    def create(self, vals):
        if vals.get("import_batch", "New") == "New":
            vals["import_batch"] = (self.env["ir.sequence"].next_by_code("drops.sequence") or "New")
        res = super(Drops_Issuance_Import, self).create(vals)
        return res        