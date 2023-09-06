# -*- coding: utf-8 -*-
{
    'name': "skycable_employee_inventory_system",
    'summary': """
        Created and modified by the Titans. Do not try to edit or you\'ll face the consequences and the wrath of titan. Goodluck to you!""",
    'description': """
        Long description of module's purpose
    """,
    'author': "WSI GANG",
    'website': "http://www.yourcompany.com",
    'category': 'Warehouse',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['base','stock','procurement','purchase','product','contacts', 'account', 'sale', 'project', 'website_partner','crm','etsi_base','etsi_hrms','etsi_payroll','website'],

    # always loaded
    'data': [
        #wizard
        'wizard/skycable_issued_wizards.xml',
        'security/ir.model.access.csv',
        'data/drop_issuance_sequence.xml',
        'data/warehouse_scheduler.xml',
        'data/skycable_inventory_adjustment_sequence.xml',
        'views/skycable_inventory_all_transfer_views.xml',
        'views/skycable_inventory_adjustment_views.xml',
        'views/skycable_inventory_operation_type_views.xml',
        'views/skycable_inventory_products_views.xml',
        'views/skycable_employee_teams_configuration.xml',
        'views/skycable_contact_configuration.xml',
        # Phase 3
        'views/skycable_operation_return.xml',
        'views/team_issuance_views.xml',
        'views/skycable_inventory_subscriber_issuance.xml',
        'views/skycable_inventory_pullout_operation.xml',
        'views/skycable_drops_issuance.xml',
        'views/skycable_transfer_list.xml',
        'views/skycable_employee_hr_dash_hide_view.xml',
        'views/skycable_employee_hr_hide_asset.xml',
        'views/skycable_employee_hr_hide_states.xml',
        'views/skycable_employee_hr_hide_smart_button.xml',
        'views/skycable_employee_default_category.xml',
        'views/skycable_employee_hr_hide_bank_account_id.xml',
        'views/skycable_employee_hr_working_time.xml',
        'views/skycable_employee_hr_settings.xml',
        'views/skycable_employee_hr_manual_attendance.xml',
        'views/sky_cable_employee_hide_birthday.xml',
        'views/skycable_product_product.xml',
        'views/skycable_inventory_internal_search.xml',
        'views/sky_cable_inventory_products_view_all_serial.xml',
        # REPORTS
        'reports/report_team_issuance.xml',
        'reports/all_report_configuration.xml',
        'reports/team_configuration_file.xml',
        'reports/view_all_serials.xml',
        'reports/data_entry_template.xml',
        'reports/report_subscriber_issuance.xml',
        'reports/report_team_return_items_print.xml',
        'reports/report_damage_return.xml',
        'reports/pull_out_recieve_print.xml',
        'reports/pull_out_delivery_print.xml',
        'reports/pull_out_delivery_form.xml',
        'reports/view_all_pull_out_form.xml',
        'reports/pull_out_delivery_form_preview.xml',
        'reports/drop_issuance_report.xml',
        'views/pivot_view_all_serial.xml',
        'views/pivot_product_view.xml',
        # WEBSITE
        'views/teamList.xml',
        'views/thanks.xml',
        'views/validation.xml',
        'views/website_form.xml',
    ]
}