# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

from warnings import filters
import frappe
from frappe.model.document import Document
from io import StringIO
from frappe.utils import cstr, cint
from frappe.desk.page.setup_wizard.setup_wizard import make_records


class TraiteLCRGeneration(Document):
    def on_submit(self):
        frappe.db.sql(
            """
            update `tabSales Invoice`
            set tsv_generated_cf = 1
            where 
                tsv_generated_cf = 0 
                and docstatus = 1 
                and (mode_of_payment_art = 'Traite' or mode_of_payment_art = 'LCR')
                and due_date <= %s
        """,
            (self.generation_date),
        )

    @frappe.whitelist()
    def generate_traite_lcr(self):
        check_reports_exist()
        f = StringIO()

        # header
        tsv, data = get_tsv(
            "Traite LCR TSV Header",
            {
                "submission_date": self.generation_date,
                "bank_account": self.company_bank_account,
            },
        )
        f.write(tsv)
        f.write("\n")

        # lines from query report
        tsv, data = get_tsv("Traite LCR TSV", {"generation_date": self.generation_date})
        if data:
            f.write(tsv)
            f.write("\n")

        # footer
        total = sum([cint(d.base_grand_total) for d in data])
        footer = "".join(
            (
                "08",
                "60",
                cstr(len(data) + 1).rjust(8, "0")[:8],
                "~" * 90,
                cstr(total).rjust(12, "0")[:12],
            )
        )
        f.write(footer)

        self.tsv_file_data = f.getvalue()
        self._attach_file()

        self.save()
        frappe.db.commit()

    def _attach_file(self):
        _file = frappe.get_doc(
            {
                "doctype": "File",
                "file_name": "{}.csv".format(self.name),
                "is_private": 1,
                "content": self.tsv_file_data,
            }
        )
        _file.save()
        self.tsv_file = _file.file_url


def get_tsv(report_name, filters):
    sql = frappe.db.get_value("Report", report_name, "query")
    data = frappe.db.sql(sql, filters, as_dict=True)
    return "\n".join(["".join(d.values()) for d in data]), data


def check_reports_exist():
    if not frappe.db.exists("Report", "Traite LCR TSV Header"):
        make_records(
            [
                {
                    "name": "Traite LCR TSV Header",
                    "report_name": "Traite LCR TSV Header",
                    "ref_doctype": "Bank Account",
                    "is_standard": "No",
                    "module": "Art Collections",
                    "report_type": "Query Report",
                    "letter_head": "Standard",
                    "disable_prepared_report": 1,
                    "prepared_report": 0,
                    "query": TRAITE_LCR_TSV_HEADER,
                    "doctype": "Report",
                    "filters": [
                        {
                            "fieldname": "submission_date",
                            "label": "Submission Date",
                            "fieldtype": "Date",
                            "mandatory": 1,
                        },
                        {
                            "fieldname": "bank_account",
                            "label": "Bank Account",
                            "fieldtype": "Link",
                            "mandatory": 0,
                            "options": "Bank Account",
                        },
                    ],
                    "columns": [],
                    "roles": [
                        {
                            "role": "System Manager",
                        },
                        {
                            "role": "Accounts Manager",
                        },
                        {
                            "role": "Accounts User",
                        },
                    ],
                }
            ]
        )

    if not frappe.db.exists("Report", "Traite LCR TSV"):
        make_records(
            [
                {
                    "name": "Traite LCR TSV",
                    "report_name": "Traite LCR TSV",
                    "ref_doctype": "Traite LCR Generation",
                    "is_standard": "No",
                    "module": "Art Collections",
                    "report_type": "Query Report",
                    "letter_head": "Standard",
                    "disable_prepared_report": 1,
                    "prepared_report": 0,
                    "query": TRAITE_LCR_TSV,
                    "doctype": "Report",
                    "filters": [
                        {
                            "fieldname": "generation_date",
                            "label": "Generation Date",
                            "fieldtype": "Date",
                            "mandatory": 1,
                        },
                    ],
                    "columns": [],
                    "roles": [
                        {
                            "role": "System Manager",
                        },
                        {
                            "role": "Accounts Manager",
                        },
                        {
                            "role": "Accounts User",
                        },
                    ],
                }
            ]
        )


TRAITE_LCR_TSV = """
        select
                '06'rcode, 
                '60'ocode,
                LPAD(CAST(1+ROW_NUMBER() over (order by creation) as CHAR),8,'0') rec_num,
                REPEAT('~',18) _18,
                SUBSTR(LPAD(coalesce(customer_name,''),24,'~'),1,24) customer_name, 
                SUBSTR(LPAD(coalesce(bank_art,''),24,'~'),1,24) bank_art, 
                case 
                    when mode_of_payment_art = 'LCR' THEN 1
                    when mode_of_payment_art = 'Traite' THEN 0
                    else 'X' end mode_of_payment_art,
                REPEAT('~',2) _2,
                SUBSTR(LPAD(coalesce(establishment_code_art,''),5,'~'),1,5) establishment_code_art, 
                SUBSTR(LPAD(coalesce(branch_code_art,''),5,'~'),1,5) branch_code_art, 
                SUBSTR(LPAD(coalesce(bank_account_no_art,''),11,'~'),1,11) bank_account_no_art, 
                SUBSTR(LPAD(''+(base_grand_total*100),12,'0'),1,12) base_grand_total,
                REPEAT('~',4) _4,
                DATE_FORMAT(due_date,'%%d%%m%%y') due_date,
                DATE_FORMAT(creation,'%%d%%m%%y') creation,
                REPEAT('~',20) _20,
                SUBSTR(LPAD(coalesce(customer,''),10,'~'),1,10) customer
        from `tabSales Invoice` tsi
        where 
            tsv_generated_cf = 0 
            and docstatus = 1 
            and due_date <= %(generation_date)s               
            and 1 = case 
                    when mode_of_payment_art like '%%LCR%%' then 1
                    when mode_of_payment_art = 'Traite' and is_traite_received_cf = 1 then 1
                else 0 end
"""

TRAITE_LCR_TSV_HEADER = """select 
                '03'rcode, 
                '60'ocode,
                LPAD('1',8,'0') rec_num,
                DATE_FORMAT(NOW(),'%%d%%m%%y') submission_date,
                SUBSTR(LPAD(coalesce(company,''),24,'~'),1,24) company, 
                SUBSTR(LPAD(coalesce(bank,''),24,'~'),1,24) bank, 
                '3' type_of_input, 'E' currency_code, 
                SUBSTR(LPAD(coalesce(establishment_code_art,''),5,'~'),1,5) establishment_code_art, 
                SUBSTR(LPAD(coalesce(branch_code,''),5,'~'),1,5) branch_code, 
                SUBSTR(LPAD(coalesce(bank_account_no,''),5,'~'),1,5) bank_account_no 
        from `tabBank Account` tba 
        where name = %(bank_account)s
"""
