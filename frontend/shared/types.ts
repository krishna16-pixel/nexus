export interface User {
  id: string;
  email: string;
  role: "seller" | "buyer";
  first_name: string;
  last_name: string;
  phone?: string | null;
  address?: string | null;
  created_at: string;
}

export interface Book {
  id: string;
  seller_id: string;
  title: string;
  author: string;
  isbn?: string | null;
  description?: string | null;
  price: string;
  stock: number;
  status: "active" | "inactive";
  created_at: string;
  updated_at: string;
  seller_name?: string;
}

export interface CartLine {
  id: string;
  book_id: string;
  book: Book;
  quantity: number;
  unit_price: string;
  line_total: string;
  available: boolean;
}

export interface Cart {
  items: CartLine[];
  subtotal: string;
  subtotals_by_seller: Record<string, string>;
  item_count: number;
}

export interface OrderItem {
  id: string;
  book_id: string;
  quantity: number;
  unit_price: string;
  title: string;
  author: string;
  line_total: string;
}

export interface ShippingAddress {
  line1: string;
  line2?: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
}

export interface Courier {
  id: string;
  name: string;
  phone?: string;
  is_active: boolean;
}

export interface Order {
  id: string;
  buyer_id: string;
  seller_id: string;
  status: string;
  payment_method: string;
  payment_status: string;
  courier_partner_id?: string | null;
  shipping: ShippingAddress;
  subtotal: string;
  items: OrderItem[];
  courier?: Courier;
  seller_rating?: SellerRating;
  courier_rating?: CourierRating;
  created_at: string;
  updated_at: string;
}

export interface SellerRating {
  id: string;
  order_id: string;
  seller_id: string;
  buyer_id: string;
  rating: number;
  comment?: string | null;
  created_at: string;
  buyer?: {
    first_name: string;
    last_name: string;
  };
}

export interface CourierRating {
  id: string;
  order_id: string;
  courier_partner_id: string;
  buyer_id: string;
  rating: number;
  comment?: string | null;
  created_at: string;
  buyer?: {
    first_name: string;
    last_name: string;
  };
}

export interface PaginationMeta {
  page: number;
  per_page: number;
  total: number;
  pages: number;
}

export interface ApiError {
  error: string;
  message: string;
  details?: Record<string, string[]>;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface CircleListing {
  id: string;
  owner_id: string;
  book_id?: string | null;
  title: string;
  author?: string | null;
  offer_type: "sell" | "rent" | "donate" | "exchange";
  price?: string | null;
  rent_fee?: string | null;
  rent_days?: number | null;
  rent_hours?: number | null;
  rent_mins?: number | null;
  description?: string | null;
  city?: string | null;
  campus?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface CircleClaim {
  id: string;
  listing_id: string;
  requester_id: string;
  message?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface SwapProposal {
  id: string;
  wanted_listing_id: string;
  offered_listing_id: string;
  proposer_id: string;
  message?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ReadingEntry {
  id: string;
  user_id: string;
  book_id?: string | null;
  title: string;
  author?: string | null;
  state: string;
  city?: string | null;
  campus?: string | null;
  created_at: string;
  updated_at: string;
  reader?: { first_name: string; last_name: string };
}

export interface BuddyMatch extends ReadingEntry {}

export interface BuddyRequestItem {
  id: string;
  requester_id: string;
  target_id: string;
  message?: string | null;
  status: string;
  created_at: string;
  requester?: { first_name: string; last_name: string };
  target?: { first_name: string; last_name: string };
}

export interface DetectiveRequest {
  id: string;
  requester_id: string;
  title: string;
  author?: string | null;
  max_price?: string | null;
  city?: string | null;
  note?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface DetectiveOffer {
  id: string;
  request_id: string;
  offerer_id: string;
  book_id?: string | null;
  price?: string | null;
  message?: string | null;
  status: string;
  created_at: string;
}

export interface PassportStamp {
  id: string;
  book_id?: string | null;
  title: string;
  author?: string | null;
  from_user_id?: string | null;
  to_user_id: string;
  listing_id?: string | null;
  note?: string | null;
  created_at: string;
}

export interface ReaderNote {
  id: string;
  book_id?: string | null;
  title?: string | null;
  author?: string | null;
  writer_id: string;
  note: string;
  created_at: string;
  updated_at: string;
  writer?: { first_name: string; last_name: string };
}

export interface UserInterests {
  id: string;
  user_id: string;
  genres?: string | null;
  favorite_authors?: string | null;
  note?: string | null;
}

export interface WishItem {
  id: string;
  user_id: string;
  book_id?: string | null;
  title: string;
  author?: string | null;
  city?: string | null;
  campus?: string | null;
  max_price?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface WishGroup {
  title: string;
  author?: string | null;
  count: number;
  members: Array<{ user_id: string; city?: string | null; campus?: string | null; created_at: string }>;
  sample: WishItem;
  bulk_eligible: boolean;
  bulk_min: number;
}

export interface PriceSuggestion {
  suggested_price: string;
  breakdown: {
    base_price: string;
    condition: string;
    condition_factor: number;
    age_years: number;
    age_factor: number;
    edition?: string | null;
    edition_factor: number;
  };
  book?: Book | null;
}

export interface Rental {
  id: string;
  listing_id: string;
  claim_id: string;
  owner_id: string;
  renter_id: string;
  start_date: string;
  due_date: string;
  returned_at?: string | null;
  return_requested_at?: string | null;
  fine_amount?: string | null;
  amount_collected?: string | null;
  payment_method?: string | null;
  payment_note?: string | null;
  status: "active" | "return_requested" | "returned";
  days_left?: number | null;
  is_overdue?: boolean;
  overdue_days?: number;
  fine_preview?: string;
  fine_due?: string;
  amount_due?: string;
  amount_to_pay?: string;
  amount_to_collect?: string;
  remaining_seconds?: number;
  time_remaining?: string | null;
  hours_left?: number | null;
  minutes_left?: number | null;
  duration?: string | null;
  renter?: { id?: string; name?: string; first_name: string; last_name: string; email: string; phone?: string | null; address?: string | null } | null;
  owner?: { id?: string; name?: string; first_name: string; last_name: string; email: string; phone?: string | null; address?: string | null } | null;
  claim?: { id: string; created_at: string; message?: string | null } | null;
  listing?: CircleListing;
  created_at: string;
  updated_at: string;
}

export interface NotificationItem {
  id: string;
  user_id: string;
  kind: string;
  title: string;
  message?: string | null;
  link?: string | null;
  ref_type?: string | null;
  ref_id?: string | null;
  is_read: boolean;
  created_at: string;
}
