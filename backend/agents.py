"""Small deterministic specialists for evidence-backed purchase reviews."""
def financial_agent(metrics):
 return {'name':'Financial Analyst','finding':f"Monthly surplus is {metrics['currency']} {metrics['disposableIncome']:,.0f}; savings cover {metrics['emergencyMonths']} months of regular expenses."}
def research_agent(product):
 return {'name':'Product Research','finding':f"Reviewed curated listing in {product.get('category','Uncategorized')}; no live retailer claims are attached."}
def price_agent(product):
 return {'name':'Price Intelligence','finding':'No verified price history is stored for this listing; price movement is not forecast.'}
def decision_agent(price,metrics,affordable):
 status='fits the monthly surplus and buffer rule' if affordable else 'would exceed the monthly surplus or reduce the basic savings buffer'
 return {'name':'Purchase Decision','finding':f"At {metrics['currency']} {price:,.2f}, the purchase {status}."}
def payment_agent(affordable):
 return {'name':'Payment Safety','finding':'Checkout can be prepared only for an affordable purchase; payer approval is required before server capture.' if affordable else 'Checkout is blocked by the affordability check.'}
def run_specialists(product,price,metrics,affordable):
 return [financial_agent(metrics),research_agent(product),price_agent(product),decision_agent(price,metrics,affordable),payment_agent(affordable)]
