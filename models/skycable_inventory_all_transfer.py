from odoo import api, fields, models
import time
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime

class EtsiTeams(models.Model):
    _inherit = "stock.picking"

    etsi_teams_id = fields.Many2one('team.configuration', string="Teams Number")
    etsi_teams_member_no = fields.Char(string="Employee Number")
    etsi_teams_member_name = fields.Many2one('hr.employee',string="Employee Name")
    etsi_teams_line_ids = fields.One2many(
    'team.replace','etsi_teams_replace_line', string='Team Members') 
    
    @api.multi
    @api.onchange('etsi_teams_member_name')
    def auto_fill_details_01_name(self): 
        for rec in self:
            database_name = self.env['hr.employee'].search([('name','=',rec.etsi_teams_member_name.name)])
            rec.etsi_teams_member_no = database_name.identification_id

    @api.multi
    @api.onchange('etsi_teams_member_no')
    def auto_fill_details_01(self): 
        for rec in self:
            database = self.env['hr.employee'].search([('identification_id','=',rec.etsi_teams_member_no)])
            database2 = self.env['team.configuration'].search([('team_number','=',database.team_number_id)])
            rec.etsi_teams_member_name = database.id
            rec.etsi_teams_id = database2.id

    @api.multi
    @api.onchange('etsi_teams_id')
    def auto_fill_details_02(self):
        table=[]
        if self.etsi_teams_member_name:
            for rec2 in self.etsi_teams_id.team_members:
                table.append((0,0,{
                'team_members_lines': rec2.team_members_lines,
                'etsi_teams_replace' :'' ,
                'etsi_teams_temporary' : '',
                }))
            self.etsi_teams_line_ids = table
        
        #FOR SELECTING TEAM CODE ONLY EMPTY EMPLOYEE NAME AND NUMBER 
        else:
            for lis in self:
                database = self.env['team.configuration'].search([('id', '=' ,lis.etsi_teams_id.id)])
                database2 = self.env['hr.employee'].search([('team_number_id','=',database.team_number)],limit=1)
                lis.etsi_teams_member_name = database2

            for rec2 in self.etsi_teams_id.team_members:
                table.append((0,0,{
                'team_members_lines': rec2.team_members_lines,
                'etsi_teams_replace' :'' ,
                'etsi_teams_temporary' : '',
                }))
            self.etsi_teams_line_ids = table
                
    @api.multi
    def do_new_transfer(self):
        res = super(EtsiTeams,self).do_new_transfer()
        for line in self.etsi_teams_line_ids:
            if line.etsi_teams_temporary is False:
                self.env['team.page.lines'].create({
                'team_page_lines':  line.team_members_lines.id,
                'team_number_team': self.etsi_teams_id.team_number,
                'transaction_number': self.name,
                'status': 'permanent',
                'createdDateHistory': datetime.today(),
            })
            else:
                self.env['team.page.lines'].create({
                    'team_page_lines':  line.etsi_teams_replace.id,
                    'team_number_team': self.etsi_teams_id.team_number,
                    'transaction_number': self.name,
                    'status': 'temporary',
                    
                    'createdDateHistory': datetime.today(),
                    'replaced_by': line.team_members_lines.name,
                })
        return res
    
    # Smartbutton functions
    etsi_subscriber_issuance = fields.Integer(compute='_subs_issuance_count')
    etsi_team_issuance = fields.Integer(compute="_team_issuance_count")
    etsi_subscriber = fields.Boolean(compute="_etsi_subscriber")
    etsi_team = fields.Boolean(compute="_etsi_team")
    etsi_team_issuance_id = fields.Many2one('stock.picking')
    
    @api.depends('picking_type_id')
    def _etsi_subscriber(self):
        for rec in self:
            rec.etsi_subscriber = False
            if rec.picking_type_id.code == 'outgoing':
                if rec.picking_type_id.subscriber_checkbox == True and rec.picking_type_id.return_picking_type_id:
                    rec.etsi_subscriber = True
                    
    @api.depends('picking_type_id')
    def _etsi_team(self):
        for rec in self:
            rec.etsi_team = False
            if rec.picking_type_id.code == 'internal':
                if rec.picking_type_id.subscriber_checkbox == False and rec.picking_type_id.return_picking_type_id:
                    rec.etsi_team = True
                
    @api.multi
    def get_subscriber_issuance(self):
        context = dict(self.env.context or {})
        context.update(create=False)
        return {
            'name': 'Subscriber Issuance',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'context': {'create':0},
            'domain': [('etsi_team_issuance_id','=',self.id)]
        }
    
    def _subs_issuance_count(self):
        data_obj = self.env['stock.picking']
        for data in self:       
            list_data = data_obj.search([('etsi_team_issuance_id','=', data.id)])
            data.etsi_subscriber_issuance = len(list_data)     
            
    def get_team_issuance(self):
        context = dict(self.env.context or {})
        context.update(create=False)
        
        return {
            'name': 'Team Issuance',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'context': {'create':0},
            'domain': ([('name', '=',self.origin)])
        }
        
    def _team_issuance_count(self): 
       for rec in self:
            rec.etsi_team_issuance = 0
            if rec.etsi_team_issuance_id:
                rec.etsi_team_issuance = 1
                
class EtsiTeamsReplace(models.Model):
    _name = "team.replace"
    
    etsi_teams_replace_line = fields.Many2one('stock.picking')
    team_members_lines = fields.Many2one('hr.employee', string="Team Member")
    etsi_teams_replace = fields.Many2one('hr.employee', string="Replaced Member")
    etsi_teams_temporary = fields.Boolean(string="Temporary Team")
    etsi_teams_member_name_copy =fields.Many2one(related = "etsi_teams_replace_line.etsi_teams_member_name")

    @api.constrains('etsi_teams_replace','etsi_teams_temporary')
    def check(self):
        if self.etsi_teams_temporary == True:
            if len(self.etsi_teams_replace) == 0:
                raise ValidationError("No Replaced Member selected!")

    @api.multi
    def write(self, vals):
        y = []
        x = self.env['team.configuration'].search([]).mapped('team_members')
        for rec in x:
            y.append(rec.team_members_lines.id)

        res = super(team_configuration_line, self).write(vals)

        if res.etsi_teams_replace:
            if self.etsi_teams_replace.id in y:
                raise ValidationError("Invalid team member")
        
        return res

    @api.onchange('etsi_teams_temporary')
    def onchange_replaced_id(self):
        for request in self:
            domain = {}
            if self.etsi_teams_temporary == True:
                if request.team_members_lines:
                    task_list = []
                    task_obj = self.env['hr.employee'].search([])
                    if task_obj:
                        for task in task_obj:
                            if task.team_number_id == request.team_members_lines.team_number_id:
                                task_list.append(task.team_number_id)
                        if task_list:
                            domain['etsi_teams_replace'] =  [('team_number_id', 'not in', task_list)]
                        else:
                            domain['etsi_teams_replace'] =  []

                return {'domain': domain}
            
    @api.onchange('etsi_teams_temporary')
    def onchange_replaced_clear(self):
        if self.etsi_teams_temporary is False:
                self.etsi_teams_replace = ""
                
    @api.multi
    @api.onchange('etsi_teams_temporary')
    def auto_fill_details_temporary(self):
        if self.etsi_teams_temporary == True:
            self.etsi_teams_replace = self.etsi_teams_member_name_copy.id ,
   