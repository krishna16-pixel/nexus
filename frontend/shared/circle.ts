import { apiFetch } from "./apiClient";
import type {
  Book,
  BuddyMatch,
  BuddyRequestItem,
  CircleClaim,
  CircleListing,
  DetectiveOffer,
  DetectiveRequest,
  NotificationItem,
  PaginationMeta,
  PassportStamp,
  PriceSuggestion,
  ReaderNote,
  ReadingEntry,
  Rental,
  UserInterests,
  WishGroup,
  WishItem,
} from "./types";

export const circleApi = {
  createListing: (data: Record<string, unknown>) =>
    apiFetch<{ listing: CircleListing }>("/circle/listings", { method: "POST", body: JSON.stringify(data) }),

  openListings: (params?: { type?: string; city?: string; campus?: string; q?: string }) => {
    const q = new URLSearchParams();
    if (params?.type) q.set("type", params.type);
    if (params?.city) q.set("city", params.city);
    if (params?.campus) q.set("campus", params.campus);
    if (params?.q) q.set("q", params.q);
    const qs = q.toString();
    return apiFetch<{ listings: CircleListing[]; count: number }>(`/circle/listings${qs ? `?${qs}` : ""}`);
  },

  myListings: () => apiFetch<{ listings: CircleListing[]; count: number }>("/circle/listings/mine"),

  closeListing: (id: string) =>
    apiFetch<{ listing: CircleListing }>(`/circle/listings/${id}/close`, { method: "PATCH", body: JSON.stringify({ status: "closed" }) }),

  claim: (id: string, message?: string) =>
    apiFetch<{ claim: CircleClaim }>(`/circle/listings/${id}/claims`, {
      method: "POST",
      body: JSON.stringify({ message }),
    }),

  claimsFor: (id: string) =>
    apiFetch<{ claims: CircleClaim[]; count: number }>(`/circle/listings/${id}/claims`),

  acceptClaim: (claimId: string) =>
    apiFetch<{ claim: CircleClaim }>(`/circle/claims/${claimId}/accept`, { method: "POST" }),

  declineClaim: (claimId: string) =>
    apiFetch<{ claim: CircleClaim }>(`/circle/claims/${claimId}/decline`, { method: "POST" }),

  proposeSwap: (data: { wanted_listing_id: string; offered_listing_id: string; message?: string }) =>
    apiFetch<{ swap: { id: string } }>("/circle/swaps", { method: "POST", body: JSON.stringify(data) }),

  swapsFor: (listingId: string) =>
    apiFetch<{ swaps: Array<{ id: string; status: string; proposer_id: string; message?: string | null }> }>(
      `/circle/listings/${listingId}/swaps`
    ),

  acceptSwap: (id: string) => apiFetch(`/circle/swaps/${id}/accept`, { method: "POST" }),

  declineSwap: (id: string) => apiFetch(`/circle/swaps/${id}/decline`, { method: "POST" }),

  passport: (params: { book_id?: string; title?: string; author?: string }) => {
    const q = new URLSearchParams();
    if (params.book_id) q.set("book_id", params.book_id);
    if (params.title) q.set("title", params.title);
    if (params.author) q.set("author", params.author);
    return apiFetch<{ book: Book | null; stamps: PassportStamp[]; reader_count: number; transfer_count: number }>(
      `/circle/passport?${q.toString()}`
    );
  },

  priceSuggest: (data: { book_id?: string; original_price?: string; condition: string; age_years?: number; edition?: string }) =>
    apiFetch<PriceSuggestion>("/circle/price-suggest", { method: "POST", body: JSON.stringify(data) }),

  markReading: (data: Record<string, unknown>) =>
    apiFetch<{ reading: ReadingEntry }>("/circle/reading", { method: "POST", body: JSON.stringify(data) }),

  myReading: () => apiFetch<{ reading: ReadingEntry[]; count: number }>("/circle/reading/mine"),

  buddies: (readingId: string) =>
    apiFetch<{ buddies: BuddyMatch[] }>(`/circle/reading/${readingId}/buddies`),

  buddyRequest: (target_id: string, message?: string) =>
    apiFetch<{ request: BuddyRequestItem }>("/circle/buddies/request", {
      method: "POST",
      body: JSON.stringify({ target_id, message }),
    }),

  buddyInbox: () => apiFetch<{ requests: BuddyRequestItem[]; count: number }>("/circle/buddies/inbox"),

  buddyDecide: (id: string, accept: boolean) =>
    apiFetch<{ request: BuddyRequestItem }>(`/circle/buddies/${id}/${accept ? "accept" : "decline"}`, { method: "POST" }),

  detectiveCreate: (data: Record<string, unknown>) =>
    apiFetch<{ request: DetectiveRequest }>("/circle/detective", { method: "POST", body: JSON.stringify(data) }),

  detectiveList: (params?: { city?: string; q?: string }) => {
    const q = new URLSearchParams();
    if (params?.city) q.set("city", params.city);
    if (params?.q) q.set("q", params.q);
    const qs = q.toString();
    return apiFetch<{ requests: DetectiveRequest[]; count: number }>(`/circle/detective${qs ? `?${qs}` : ""}`);
  },

  detectiveOffer: (id: string, data: Record<string, unknown>) =>
    apiFetch<{ offer: DetectiveOffer }>(`/circle/detective/${id}/offers`, { method: "POST", body: JSON.stringify(data) }),

  detectiveOffers: (id: string) =>
    apiFetch<{ offers: DetectiveOffer[]; count: number }>(`/circle/detective/${id}/offers`),

  detectiveAccept: (offerId: string) =>
    apiFetch<{ offer: DetectiveOffer }>(`/circle/detective/offers/${offerId}/accept`, { method: "POST" }),

  saveInterests: (data: { genres?: string; favorite_authors?: string; note?: string }) =>
    apiFetch<{ interests: UserInterests }>("/circle/interests", { method: "PUT", body: JSON.stringify(data) }),

  mystery: () => apiFetch<{ book: Book; reason: string; matched_terms: string[] }>("/circle/mystery"),

  addNote: (data: { book_id?: string; title?: string; author?: string; note: string }) =>
    apiFetch<{ note: ReaderNote }>("/circle/notes", { method: "POST", body: JSON.stringify(data) }),

  notesForBook: (book_id: string) =>
    apiFetch<{ notes: ReaderNote[]; count: number }>(`/circle/notes?book_id=${book_id}`),

  deleteNote: (id: string) => apiFetch<void>(`/circle/notes/${id}`, { method: "DELETE" }),

  wishAdd: (data: Record<string, unknown>) =>
    apiFetch<{ wish: WishItem }>("/circle/wishlist", { method: "POST", body: JSON.stringify(data) }),

  wishGroups: () => apiFetch<{ groups: WishGroup[] }>("/circle/wishlist/groups"),

  wishMine: () => apiFetch<{ wishes: WishItem[]; count: number }>("/circle/wishlist/mine"),

  wishClose: (id: string) =>
    apiFetch<{ wish: WishItem }>(`/circle/wishlist/${id}/close`, { method: "PATCH", body: JSON.stringify({ status: "closed" }) }),

  myRentals: () => apiFetch<{ rentals: Rental[]; count: number }>("/circle/rentals/mine"),

  rentedOut: () => apiFetch<{ rentals: Rental[]; count: number }>("/circle/rentals/out"),

  getRental: (id: string) => apiFetch<{ rental: Rental }>(`/circle/rentals/${id}`),

  requestReturn: (id: string) =>
    apiFetch<{ rental: Rental }>(`/circle/rentals/${id}/return`, { method: "POST" }),

  cancelReturn: (id: string) =>
    apiFetch<{ rental: Rental }>(`/circle/rentals/${id}/return/cancel`, { method: "POST" }),

  confirmReturn: (id: string) =>
    apiFetch<{ rental: Rental }>(`/circle/rentals/${id}/return/confirm`, { method: "POST" }),

  completeReturn: (id: string, data: Record<string, unknown>) =>
    apiFetch<{ rental: Rental }>(`/circle/rentals/${id}/complete`, { method: "POST", body: JSON.stringify(data) }),

  applyFine: (id: string) =>
    apiFetch<{ rental: Rental }>(`/circle/rentals/${id}/fine`, { method: "POST" }),

  notifications: (params?: { page?: number; unread_only?: boolean }) => {
    const q = new URLSearchParams();
    if (params?.page) q.set("page", String(params.page));
    if (params?.unread_only) q.set("unread_only", "1");
    const qs = q.toString();
    return apiFetch<{ notifications: NotificationItem[]; meta: PaginationMeta; unread_count: number }>(
      `/circle/notifications${qs ? `?${qs}` : ""}`
    );
  },

  unreadCount: () => apiFetch<{ unread: number }>("/circle/notifications/unread-count"),

  markNotificationRead: (id: string) =>
    apiFetch<{ notification: NotificationItem }>(`/circle/notifications/${id}/read`, { method: "POST" }),

  markAllNotificationsRead: () =>
    apiFetch<{ marked: number }>("/circle/notifications/read-all", { method: "POST" }),
};
