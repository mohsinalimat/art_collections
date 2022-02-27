# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

from warnings import filters
import frappe
from frappe.model.document import Document
from io import StringIO
from frappe.utils import cstr, cint


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
        f = StringIO()
        # header
        f.write(self.get_header())
        f.write("\n")

        # lines from query report
        sql = frappe.db.get_value("Report", "Traite LCR TSV", "query")
        data = frappe.db.sql(
            sql, {"generation_date": self.generation_date}, as_dict=True
        )

        f.write("\n".join(["".join(d.values()) for d in data]))
        f.write(data and "\n" or "")

        # footer
        total = sum([cint(d.base_grand_total) for d in data])
        footer = (
            "08"
            + "60"
            + cstr(len(data) + 1).rjust(5, "0")[:5]
            + "~" * 90
            + cstr(total).rjust(12, "0")[:12]
        )
        f.write(footer)

        self.tsv_file_data = f.getvalue()
        self._attach_file()

        self.save()
        frappe.db.commit()

    def get_header(self):
        return "036000000001            030222ARTYFĘTES FACTORY       BRED CAEN ST ETIENNE    3 E101070036900530696023"

    def _attach_file(self):
        _file = frappe.get_doc(
            {
                "doctype": "File",
                "file_name": "{}.tsv".format(self.name),
                "is_private": 1,
                "content": self.tsv_file_data,
            }
        )
        _file.save()
        self.tsv_file = _file.file_url

    # def get_data(self):
    # data = frappe.db.sql(
    #     """
    # select
    #     CONCAT(
    #         '06',
    #         '60',
    #         LPAD(CAST(1+ROW_NUMBER() over (order by creation) as CHAR),8,'0'),
    #         REPEAT(' ',18),
    #         SUBSTR(LPAD(coalesce(customer_name,''),24,' '),1,24),
    #         SUBSTR(LPAD(coalesce(bank_art,''),24,' '),1,24),
    #         case
    #             when mode_of_payment_art = 'LCR' THEN 1
    #             when mode_of_payment_art = 'Traite' THEN 0
    #             else 'X' end,
    #         REPEAT(' ',2),
    #         SUBSTR(LPAD(coalesce(establishment_code_art,''),5,' '),1,5),
    #         SUBSTR(LPAD(coalesce(branch_code_art,''),5,' '),1,5),
    #         SUBSTR(LPAD(coalesce(bank_account_no_art,''),11,' '),1,11),
    #         SUBSTR(LPAD(''+(base_grand_total*100),12,'0'),1,12),
    #         REPEAT(' ',4),
    #         DATE_FORMAT(due_date,'%%d%%m%%y'),
    #         DATE_FORMAT(creation,'%%d%%m%%y'),
    #         REPEAT(' ',20),
    #         SUBSTR(LPAD(coalesce(customer,''),10,' '),1,10)
    #     ) line,
    #     cast(base_grand_total * 100 as int) base_grand_total
    # from `tabSales Invoice` tsi
    # where
    #     tsv_generated_cf = 0
    #     and docstatus = 1
    #     and (mode_of_payment_art = 'Traite' or mode_of_payment_art = 'LCR')
    #     and due_date <= %s
    # """,
    #     (self.generation_date),
    #     as_dict=True,
    # )
