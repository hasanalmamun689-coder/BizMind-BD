export type UserRole = "owner" | "store_manager";

export interface User {
  id: number;
  business_id: number;
  full_name: string;
  email: string;
  role: UserRole;
}

export interface Product {
  id: number;
  business_id: number;
  name: string;
  sku: string | null;
  brand: string | null;
  unit: string | null;
  category_id: number | null;
  supplier_id: number | null;
  purchase_price: string;
  selling_price: string;
  current_stock: number;
  minimum_stock: number;
  maximum_stock: number | null;
  status: string;
}

export interface Supplier {
  id: number;
  business_id: number;
  name: string;
  contact: string | null;
  location: string | null;
  delivery_time_days: number | null;
  reliability_score: string | null;
  payment_terms: string | null;
}

export interface SaleItemInput {
  product_id: number;
  quantity: number;
  unit_price: number;
}

export interface Sale {
  id: number;
  customer_id: number | null;
  total_amount: string;
  status: string;
  sold_at: string;
  items: { id: number; product_id: number; quantity: number; unit_price: string; line_total: string }[];
}

export interface DashboardSummary {
  total_sales: string;
  total_profit_estimate: string;
  inventory_value: string;
  low_stock_count: number;
  business_health_score: number;
}

export interface StockAlert {
  product_id: number;
  product_name: string;
  current_stock: number;
  minimum_stock: number;
  average_daily_sales: number;
  predicted_days_to_stockout: number | null;
}

export interface PurchaseOrder {
  id: number;
  po_number: string;
  supplier_id: number;
  status: string;
  total_cost: string;
  reason: string | null;
  items: { id: number; product_id: number; quantity: number; unit_cost: string; line_total: string }[];
}

export interface Expense {
  id: number;
  category: string;
  amount: string;
  description: string | null;
  incurred_on: string;
}
