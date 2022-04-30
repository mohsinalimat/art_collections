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
        data = get_records(
            "Traite LCR TSV Header",
            {
                "submission_date": self.generation_date,
                "bank_account": self.company_bank_account,
            },
        )
        tsv = get_header(data)
        f.write(tsv)
        f.write("\n")

        # lines from query report
        data = get_records("Traite LCR TSV", {"generation_date": self.generation_date})
        tsv = get_lines(data)
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
                " " * 90,
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
                "content": self.tsv_file_data.replace("~", ""),
            }
        )
        _file.save()
        self.tsv_file = _file.file_url


def get_records(
    report_name,
    filters,
):
    sql = frappe.db.get_value("Report", report_name, "query")
    return frappe.db.sql(sql, filters, as_dict=True)


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
                1+ROW_NUMBER() over (order by creation) rec_num,
                customer_name, 
                bank_art, 
                case 
                    when mode_of_payment_art = 'LCR' THEN 1
                    when mode_of_payment_art = 'Traite' THEN 0
                    else 'X' end mode_of_payment_art,
                establishment_code_art, 
                branch_code_art, 
                bank_account_no_art, 
                cast(base_grand_total*100 as int) base_grand_total,
                DATE_FORMAT(due_date,'%%d%%m%%y') due_date,
                DATE_FORMAT(creation,'%%d%%m%%y') creation,
                customer
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
                1 rec_num,
                DATE_FORMAT(NOW(),'%%d%%m%%y') submission_date,
                company, 
                bank, 
                '3' type_of_input, 
                'E' currency_code, 
                establishment_code_art, 
                branch_code, 
                bank_account_no 
        from `tabBank Account` tba 
        where name = %(bank_account)s
"""


def get_header(data):
    fmt = {
        "rcode": "03",
        "ocode": "60",
        "rec_num": "00000001",
        "filler1": " " * 12,
        "submission_date": 6,
        "company": 24,
        "bank": 24,
        "type_of_input": "3 ",
        "currency_code": 1,
        "establishment_code_art": 5,
        "branch_code": 5,
        "bank_account_no": 11,
    }
    out = ""
    for d in data:
        for col in fmt:
            if isinstance(fmt[col], str):
                out = out + fmt[col]
            elif col == "bank_account_no":
                out = out + cstr(d.get(col)).rjust(fmt[col], "0")
            else:
                out = out + cstr(d.get(col)).ljust(fmt[col], " ")
    return out


def get_lines(data):
    fmt = {
        "rcode": "06",
        "ocode": "60",
        "rec_num": 8,
        "filler_1": " " * 18,
        "customer_name": 24,
        "bank_art": 24,
        "mode_of_payment_art": 1,
        "filler_2": " " * 2,
        "establishment_code_art": 5,
        "branch_code_art": 5,
        "bank_account_no_art": 11,
        "base_grand_total": 12,
        "filler_3": " " * 4,
        "due_date": 6,
        "creation": 6,
        "filler_4": " " * 20,
        "customer": 10,
    }
    out = ""
    for d in data:
        for col in fmt:
            if isinstance(fmt[col], str):
                out = out + fmt[col]
            elif col in (
                "rec_num",
                "base_grand_total",
            ):
                out = out + cstr(d.get(col)).rjust(fmt[col], "0")
            elif col in (
                "bank_account_no_art",
                "customer",
            ):
                out = out + cstr(d.get(col)).rjust(fmt[col], " ")
            else:
                out = out + cstr(d.get(col)).ljust(fmt[col], " ")
    return out
