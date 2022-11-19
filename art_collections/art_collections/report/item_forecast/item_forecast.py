from distutils.log import debug
import frappe
from frappe import _
from frappe.utils import get_year_start,add_months,get_first_day,get_last_day

def execute(filters=None):
	columns, data = [], []
	return get_columns(filters), get_data(filters)

def get_data(filters=None):
	#  first_day_of_year(get_year_from(to_date)) ex. 01/01/2022 
	#  first_day_of_month((to_date) - 12 months)
	#  last_day_of_month((to_date) - 12 months)
	if filters.to_date:
		year_start_date=get_year_start(filters.to_date)
		month_start_date=get_first_day(add_months(filters.to_date,-12))
		month_end_date=get_last_day(add_months(filters.to_date,-12))

	data = frappe.db.sql(
		"""with fn as (
SELECT  
item.name,
item.item_code ,
item.item_name,  
item.disabled,
item.is_stock_item,
item.is_sales_item ,
item.is_purchase_item ,
ucd.conversion_factor as inner_conversion_factor,
item.availability_date_art 
from `tabItem` as item
left outer join `tabUOM Conversion Detail` ucd
on ucd.parent = item.name and ucd.uom = (select value from `tabSingles` where doctype='Art Collections Settings' and field='inner_carton_uom')
group by item.name 
),
customer_revenue as 
(
	SELECT SI.customer,sum(SI.base_net_total) as customer_revenue_for_last_12_months
	FROM `tabSales Invoice Item` SI_item 
	inner join `tabSales Invoice` SI on SI.name = SI_item.parent 
	where SI.posting_date > DATE_ADD(%(to_date)s,INTERVAL -12 MONTH) 
	and SI.docstatus =1
	group by SI.customer
	ORDER by customer_revenue_for_last_12_months desc limit 10
),
item_customer_pair as(select SI_item.item_code , GROUP_CONCAT(DISTINCT customer_revenue.customer) customer
from customer_revenue
inner join `tabSales Invoice` SI on SI.customer = customer_revenue.customer
inner join `tabSales Invoice Item` SI_item on SI_item.parent = SI.name 
where SI.posting_date > DATE_ADD(%(to_date)s,INTERVAL -12 MONTH) 
and SI.docstatus =1
group by SI_item.item_code),
col_catalogue_type as (SELECT GROUP_CONCAT(DISTINCT catalogue_directory_parent.catalogue_type) as catalogue_type,
universe_item.item FROM 
`tabCatalogue Directory Art` catalogue_directory_parent 
left outer join 
`tabCatalogue Directory Art` catalogue_directory 
on catalogue_directory_parent.lft < catalogue_directory.lft and catalogue_directory_parent.rgt > catalogue_directory.rgt 
inner join `tabItem Universe Page Art` universe_item
on  universe_item.parent = catalogue_directory.name
where catalogue_directory_parent.node_type='Catalogue'
and catalogue_directory.node_type='Universe'
group by universe_item.item
),
col_supplier as (select GROUP_CONCAT(DISTINCT supplier) as supplier, pr_item.item_code
from `tabPurchase Receipt` pr inner join `tabPurchase Receipt Item` pr_item on pr.name=pr_item.parent
where pr.docstatus =1
group by pr_item.item_code
),
col_i as (SELECT SI_item.item_code ,SUM(SI_item.stock_qty) as qty_sold_in_financial_year ,
case when ROW_NUMBER() over (order by SUM(SI_item.stock_qty)DESC )< 101 then 'Qté' else '' end as notion_qty
FROM `tabSales Invoice Item` SI_item 
inner join `tabSales Invoice` SI on SI.name = SI_item.parent 
where SI.posting_date >= %(year_start_date)s
and SI.docstatus =1
group by SI_item.item_code 
order by SUM(SI_item.stock_qty) DESC
),
col_price_buying as (SELECT  tip.price_list_rate,tip.item_code,
ROW_NUMBER() over (PARTITION by tip.item_code order by tip.valid_from DESC   ) as rn
from `tabItem Price` tip 
where tip.price_list =(select value from `tabSingles` where doctype='Buying Settings' and field='buying_price_list')
and %(to_date)s between ifnull(tip.valid_from, '2000-01-01') and ifnull(tip.valid_upto, '2500-12-31')
group by tip.item_code 
),
col_rev_fy as (SELECT SI_item.item_code,SUM(SI_item.net_amount)   as revenue_in_financial_year ,
case when ROW_NUMBER() over (order by SUM(SI_item.net_amount) )< 101 then 'CA' else '' end as notion_ca
FROM `tabSales Invoice Item` SI_item 
inner join `tabSales Invoice` SI on SI.name = SI_item.parent 
where SI.posting_date >= %(year_start_date)s
and SI.docstatus =1
group by SI_item.item_code 
order by SUM(SI_item.stock_qty) DESC
),
col_l as (SELECT SI_item.item_code ,SUM(SI_item.stock_qty)/12 as avg_qty_sold_per_month 
FROM `tabSales Invoice Item` SI_item 
inner join `tabSales Invoice` SI on SI.name = SI_item.parent 
where SI.posting_date > DATE_ADD(%(to_date)s,INTERVAL -12 MONTH)
and SI.docstatus =1
group by SI_item.item_code ),
col_k as (SELECT SI_item.item_code ,SUM(SI_item.stock_qty) as qty_sold_in_last_12_months ,
case when ROW_NUMBER() over (order by SUM(SI_item.stock_qty)DESC )< 101 then 'Qté' else '' end as notion_qty
FROM `tabSales Invoice Item` SI_item 
inner join `tabSales Invoice` SI on SI.name = SI_item.parent 
where SI.posting_date > DATE_ADD(%(to_date)s,INTERVAL -12 MONTH)
and SI.docstatus =1
group by SI_item.item_code 
order by SUM(SI_item.stock_qty) DESC
),
col_j as (SELECT SI_item.item_code,SUM(SI_item.net_amount)   as revenue_for_last_12_months ,
case when ROW_NUMBER() over (order by SUM(SI_item.net_amount) )< 101 then 'CA' else '' end as notion_ca
FROM `tabSales Invoice Item` SI_item 
inner join `tabSales Invoice` SI on SI.name = SI_item.parent 
where SI.posting_date > DATE_ADD(%(to_date)s,INTERVAL -12 MONTH) 
and SI.docstatus =1
group by SI_item.item_code  
order by SUM(SI_item.net_amount) DESC 
),
col_m as (SELECT item_code,COALESCE(total_qty_in_purchase_order_cf,0) as total_po_qty_to_be_received FROM `tabItem`),
col_o as (SELECT item_code,COALESCE(saleable_qty_cf,0) as total_saleable_stock FROM `tabItem`),
col_p as (SELECT item_code,COALESCE(qty_sold_to_deliver_cf,0) as qty_sold_to_be_delivered FROM `tabItem`),
col_s as (SELECT  PR_item.item_code ,TIMESTAMPDIFF(MONTH,PR.posting_date,NOW())  as months_since_first_purchase_receipt,
ROW_NUMBER() over (PARTITION by PR_item.item_code order by PR.posting_date desc ) as rn
FROM  `tabPurchase Receipt` as PR
inner join `tabPurchase Receipt Item` PR_item
on PR.name =PR_item.parent 
where PR.docstatus =1
),
col_restock_qty_by_shipping as (SELECT  SI_item.item_code , SUM(SI_item.stock_qty) as total_quantity_sold_restocking 
FROM  `tabSales Invoice Item` as SI_item
inner join `tabSales Invoice` as SI 
on SI.name =SI_item.parent 
where SI.docstatus = 1
and SI.cycle_status_art='Restocking'
and SI.shipping_address is not NULL 
and SI.posting_date <= %(to_date)s
group by SI_item.item_code,SI.shipping_address
),
col_nbr_billing_add_ordered_1_time as (SELECT  SI_item.item_code , COUNT(SI.name) as nbr_billing_add_ordered_1_time 
FROM  `tabSales Invoice Item` as SI_item
inner join `tabSales Invoice` as SI 
on SI.name =SI_item.parent 
where SI.docstatus = 1
and SI.customer_address  is not NULL 
and SI.posting_date <= %(to_date)s
group by SI_item.item_code
),
col_nbr_shipping_add_ordered_1_time as (SELECT  SI_item.item_code , COUNT(SI.name) as nbr_shipping_add_ordered_1_time 
FROM  `tabSales Invoice Item` as SI_item
inner join `tabSales Invoice` as SI 
on SI.name =SI_item.parent 
where SI.docstatus = 1
and SI.shipping_address  is not NULL 
and SI.posting_date <= %(to_date)s
group by SI_item.item_code
),
col_total_quantity_sold as (SELECT  SI_item.item_code , SUM(SI_item.stock_qty) as total_quantity_sold
FROM  `tabSales Invoice Item` as SI_item
inner join `tabSales Invoice` as SI 
on SI.name =SI_item.parent 
where SI.docstatus = 1
and SI.posting_date <= %(to_date)s
group by SI_item.item_code
),
col_u_last_month as (SELECT  SI_item.item_code , SUM(SI_item.stock_qty) as last_year_same_month_stock 
FROM  `tabSales Invoice Item` as SI_item
inner join `tabSales Invoice` as SI 
on SI.name =SI_item.parent 
where SI.docstatus = 1
and (SI.posting_date BETWEEN %(month_start_date)s and %(month_end_date)s)
group by SI_item.item_code )
SELECT 
col_supplier.supplier,fn.item_code,fn.item_name,col_catalogue_type.catalogue_type,fn.disabled,fn.is_stock_item,fn.is_sales_item,fn.is_purchase_item,fn.inner_conversion_factor,
CONCAT(col_j.notion_ca,' ',col_k.notion_qty) as best_amt_qty,
col_i.qty_sold_in_financial_year,
col_rev_fy.revenue_in_financial_year,
col_price_buying.price_list_rate as last_purchase_rate,
col_restock_qty_by_shipping.total_quantity_sold_restocking as total_quantity_sold_restocking,
col_nbr_billing_add_ordered_1_time.nbr_billing_add_ordered_1_time as nbr_billing_address_ordered_1_time,
col_nbr_shipping_add_ordered_1_time.nbr_shipping_add_ordered_1_time as nbr_shipping_address_ordered_1_time,
col_total_quantity_sold.total_quantity_sold as total_quantity_sold,
col_j.revenue_for_last_12_months,
col_k.qty_sold_in_last_12_months,
col_l.avg_qty_sold_per_month,
col_m.total_po_qty_to_be_received,
fn.availability_date_art,
col_o.total_saleable_stock,
col_p.qty_sold_to_be_delivered,
col_o.total_saleable_stock-col_p.qty_sold_to_be_delivered as stock_disposable,
(col_o.total_saleable_stock-col_p.qty_sold_to_be_delivered)/NULLIF(col_l.avg_qty_sold_per_month,0)  as nbr_mois,
col_s.months_since_first_purchase_receipt,
((col_l.avg_qty_sold_per_month*8)+col_p.qty_sold_to_be_delivered)-(col_o.total_saleable_stock+col_m.total_po_qty_to_be_received) as commander,
IF((col_s.months_since_first_purchase_receipt<=12),
(col_l.avg_qty_sold_per_month+((col_l.avg_qty_sold_per_month*8)+col_p.qty_sold_to_be_delivered)-(col_o.total_saleable_stock+col_m.total_po_qty_to_be_received)),
(((col_l.avg_qty_sold_per_month*8)+col_p.qty_sold_to_be_delivered)-(col_o.total_saleable_stock+col_m.total_po_qty_to_be_received)+col_u_last_month.last_year_same_month_stock ))
as col_u,
item_customer_pair.customer as best_customer
from fn left outer join col_l on col_l.item_code = fn.name 
left outer join col_i on col_i.item_code =fn.name 
left outer join col_rev_fy on col_rev_fy.item_code =fn.name 
left outer join col_price_buying on col_price_buying.item_code =fn.name and col_price_buying.rn=1
left outer join col_k on col_k.item_code =fn.name 
left outer join col_j on col_j.item_code =fn.name 
left outer join col_m on col_m.item_code =fn.name
left outer join col_o on col_o.item_code =fn.name  
left outer join col_p on col_p.item_code =fn.name 
left outer join col_s on col_s.item_code =fn.name and col_s.rn=1
left outer join col_restock_qty_by_shipping on col_restock_qty_by_shipping.item_code =fn.name 
left outer join col_nbr_billing_add_ordered_1_time on col_nbr_billing_add_ordered_1_time.item_code =fn.name 
left outer join col_nbr_shipping_add_ordered_1_time on col_nbr_shipping_add_ordered_1_time.item_code =fn.name 
left outer join col_total_quantity_sold on col_total_quantity_sold.item_code =fn.name 
left outer join col_u_last_month on col_u_last_month.item_code =fn.name 
left outer join col_supplier on col_supplier.item_code=fn.name
left outer join item_customer_pair on item_customer_pair.item_code=fn.name
left outer join col_catalogue_type on col_catalogue_type.item=fn.name
""",		values = {
			'from_date': filters.from_date,
			'to_date': filters.to_date,
			'year_start_date':year_start_date,
			'month_start_date':month_start_date,
			'month_end_date':month_end_date
		},as_dict=1)
	return data


def get_columns(filters):
	columns = [
		{
			"label": _("Fournisseur"),
			"fieldname": "supplier",
			"width": 200
		},
		{
			"label": _("Code article"),
			"fieldtype": "Link",
			"fieldname": "item_code",
			"options": "Item",
			"width": 220
		},
		{
			"label": _("Catalogue (type)"),
			"fieldname": "catalogue_type",
			"width": 200
		},	
        {
            "label": _("Désactivé"),
            "fieldtype": "Int",
            "fieldname": "disabled",
            "width": 50
        },      
        {
            "label": _("Maintenir stock"),
            "fieldtype": "Int",
            "fieldname": "is_stock_item",
            "width": 50
        }, 		
		{
			"label": _("A la vente"),
			"fieldtype": "Int",
			"fieldname": "is_sales_item",
			"width": 50
		},	
		{
			"label": _("A l'achat"),
			"fieldtype": "Int",
			"fieldname": "is_purchase_item",
			"width": 50
		},	
		{
			"label": _("Colisage (Inner)"),
			"fieldtype": "Int",
			"fieldname": "inner_conversion_factor",
			"width": 50
		},
		{
			"label": _("Best"),
			"fieldname": "best_amt_qty",
			"width": 200
		},	
		{
			"label": _("Qty vendue depuis janvier"),
			"fieldtype": "Float",
			"fieldname": "qty_sold_in_financial_year",
			"width": 120
		},	
		{
			"label": _("Qty vendue depuis 12 mois"),
			"fieldtype": "Float",
			"fieldname": "qty_sold_in_last_12_months",
			"width": 120
		},
		{
			"label": _("CA depuis janvier"),
			"fieldtype": "Currency",
			"fieldname": "revenue_in_financial_year",
			"options": "currency",
			"width": 120
		},		
		{
			"label": _("CA  depuis12 mois"),
			"fieldtype": "Currency",
			"fieldname": "revenue_for_last_12_months",
			"options": "currency",
			"width": 120
		},
															
		{
			"label": _("Qté vente moyenne par mois"),
			"fieldtype": "Float",
			"fieldname": "avg_qty_sold_per_month",
			"width": 140
		},
		{
			"label": _("Total appro"),
			"fieldtype": "Float",
			"fieldname": "total_po_qty_to_be_received",
			"width": 140
		},		
		{
			"label": _("Date prochaine appro"),
			"fieldtype": "Date",
			"fieldname": "availability_date_art",
			"width": 140
		},
		{
			"label": _("Saleable Stock"),
			"fieldtype": "Float",
			"fieldname": "total_saleable_stock",
			"width": 140
		},	
		{
			"label": _("Résa client"),
			"fieldtype": "Float",
			"fieldname": "qty_sold_to_be_delivered",
			"width": 140
		},		
		{
			"label": _("Stock disponible"),
			"fieldtype": "Float",
			"fieldname": "stock_disposable",
			"width": 140
		},	
		{
			"label": _("Nbr mois Couverture"),
			"fieldtype": "Float",
			"fieldname": "nbr_mois",
			"width": 140
		},	
		{
			"label": _("Nbr mois d'ancienneté"),
			"fieldtype": "Int",
			"fieldname": "months_since_first_purchase_receipt",
			"width": 50
		},	
        {
            "label": _("Dernier prix d'achat"),
            "fieldtype": "Currency",
            "fieldname": "last_purchase_rate",
            "options": "currency",
            "width": 120
        },	
		{
			"label": _("Nbr client commande 1 fois"),
			"fieldtype": "Int",
			"fieldname": "nbr_billing_address_ordered_1_time",
			"width": 50
		},		
		{
			"label": _("Nbr PV commande 1 fois"),
			"fieldtype": "Int",
			"fieldname": "nbr_shipping_address_ordered_1_time",
			"width": 50
		},	
		{
			"label": _("Total quantité vendue"),
			"fieldtype": "Float",
			"fieldname": "total_quantity_sold",
			"width": 140
		},
		{
			"label": _("Total quantité vendue en réassort"),
			"fieldtype": "Float",
			"fieldname": "total_quantity_sold_restocking",
			"width": 140
		},										
	    {
            "label": _("Meilleurs clients"),
            "fieldname": "best_customer",
            "width": 200
        },							
		{
			"label": _("Proposition réassort"),
			"fieldtype": "Float",
			"fieldname": "commander",
			"width": 140
		},	
		{
			"label": _("Proposition réassort M+1"),
			"fieldtype": "Float",
			"fieldname": "col_u",
			"width": 140
		}																						
	]

	return columns	