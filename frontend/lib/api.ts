const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type VerificationStatus =
  | "unverified"
  | "pending"
  | "verified"
  | "rejected";

export type BookerType = "individual" | "group";

export interface User {
  id: string;
  email: string;
  is_booker: boolean;
  is_act_owner: boolean;
  is_act_manager: boolean;
  is_booking_coordinator: boolean;
  manager_verified: boolean;
  booker_experience_level: number | null;
  booker_type: BookerType;
  group_name: string | null;
  group_size: number | null;
  is_admin: boolean;
  verification_status: VerificationStatus;
  is_minor: boolean;
  created_at: string;
  first_name: string;
  last_name: string;
  avatar_url?: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export type ActivityType = "private_gig" | "corporate" | "wedding" | "festival";

export type Genre = "jazz" | "rock" | "pop" | "country" | "classical";

export interface ActCategory {
  id: string;
  name: string;
  active_in_ui: boolean;
}

export interface OfferingSummary {
  id: string;
  act_id: string;
  act_name: string;
  act_category_id: string;
  activity_type: ActivityType;
  price: string;
  availability: string | null;
  promoter_only_allowed: boolean;
  slug: string;
  display_location: string;
  public_lat: number;
  public_lng: number;
  photo_urls: string[];
  genres: Genre[];
  created_at: string;
}

export interface OfferingDetail extends OfferingSummary {
  act_owner_id: string;
  description: string | null;
  act_type: string | null;
  active: boolean;
}

export interface Act {
  id: string;
  act_owner_id: string;
  act_category_id: string;
  name: string;
  act_type: string | null;
  years_active: number | null;
  description: string | null;
  lat: number;
  lng: number;
  address: string;
  photo_urls: string[];
  genres: Genre[];
  created_at: string;
}

export interface ActOwnerOffering {
  id: string;
  act_id: string;
  act_owner_id: string;
  activity_type: ActivityType;
  price: string;
  availability: string | null;
  promoter_only_allowed: boolean;
  active: boolean;
  slug: string;
  display_location: string;
  min_booker_experience: number | null;
  max_venue_capacity: number | null;
  sound_system_required: boolean;
  equipment_provided: string;
  created_at: string;
}

export interface AdminStats {
  total_users: number;
  admin_users: number;
  verified_users: number;
  unverified_users: number;
  pending_users: number;
  rejected_users: number;
  booker_users: number;
  act_owner_users: number;
  manager_users: number;
  verified_manager_users: number;
  oauth_users: number;
  signups_last_7d: number;
  total_acts: number;
  total_offerings: number;
  active_offerings: number;
}

export interface AdminOfferingSummary {
  id: string;
  act_name: string;
  act_owner_email: string;
  activity_type: string;
  price: string;
  availability: string | null;
  active: boolean;
  created_at: string;
}

export interface AdminOfferingListResponse {
  items: AdminOfferingSummary[];
  total: number;
}

export interface AdminUserSummary {
  id: string;
  email: string;
  is_booker: boolean;
  is_act_owner: boolean;
  is_act_manager: boolean;
  is_booking_coordinator: boolean;
  manager_verified: boolean;
  booker_experience_level: number | null;
  is_admin: boolean;
  verification_status: VerificationStatus;
  is_minor: boolean;
  oauth_providers: string[];
  created_at: string;
}

export interface OAuthAccountSummary {
  provider: string;
  provider_email: string | null;
  provider_email_verified: boolean;
  created_at: string;
}

export interface AdminGuardianSummary {
  id: string;
  email: string;
  verification_status: VerificationStatus;
}

export interface AdminUserDetail extends AdminUserSummary {
  phone: string | null;
  guardian_user_id: string | null;
  guardian: AdminGuardianSummary | null;
  oauth_accounts: OAuthAccountSummary[];
  act_count: number;
  offering_count: number;
  active_offering_count: number;
}

export interface AdminAuditLogEntry {
  id: string;
  actor_id: string;
  actor_email: string;
  action: string;
  target_user_id: string | null;
  target_user_email: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface AdminAuditLogListResponse {
  items: AdminAuditLogEntry[];
  total: number;
  limit: number;
  offset: number;
}

export interface AdminUserListResponse {
  items: AdminUserSummary[];
  total: number;
  limit: number;
  offset: number;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function parseError(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: string | { msg: string }[] };
    if (typeof data.detail === "string") {
      return data.detail;
    }
    if (Array.isArray(data.detail) && data.detail[0]?.msg) {
      return data.detail[0].msg;
    }
  } catch {
    // ignore parse errors
  }
  return "Request failed";
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null,
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    throw new ApiError(await parseError(response), response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function registerUser(
  payload: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    is_booker: boolean;
    is_act_owner: boolean;
  },
  funnel?: { src?: string; ref?: string },
): Promise<User> {
  const search = new URLSearchParams();
  if (funnel?.src) search.set("src", funnel.src);
  if (funnel?.ref) search.set("ref", funnel.ref);
  const query = search.toString();
  const path = query ? `/auth/register?${query}` : "/auth/register";
  return request<User>(path, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function loginUser(payload: {
  email: string;
  password: string;
}): Promise<TokenResponse> {
  return request<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchCurrentUser(token: string): Promise<User> {
  return request<User>("/auth/me", {}, token);
}

export function updateProfile(
  token: string,
  payload: {
    is_act_manager?: boolean;
    is_booking_coordinator?: boolean;
    booker_experience_level?: number | null;
  },
): Promise<User> {
  return request<User>(
    "/auth/me/profile",
    { method: "PATCH", body: JSON.stringify(payload) },
    token,
  );
}

export interface GroupMember {
  id: string;
  display_name: string;
  booker_experience_level: number | null;
  is_minor: boolean;
  sort_order: number;
  created_at: string;
}

export interface GroupProfile {
  booker_type: BookerType;
  group_name: string | null;
  group_size: number | null;
  members: GroupMember[];
}

export interface GroupMemberInput {
  display_name: string;
  booker_experience_level?: number | null;
  is_minor?: boolean;
  sort_order?: number;
}

export function fetchGroupProfile(token: string): Promise<GroupProfile> {
  return request<GroupProfile>("/auth/me/group-members", {}, token);
}

export function updateGroupProfile(
  token: string,
  payload: {
    booker_type: BookerType;
    group_name?: string | null;
    group_size?: number | null;
    members?: GroupMemberInput[] | null;
  },
): Promise<GroupProfile> {
  return request<GroupProfile>(
    "/auth/me/group-profile",
    { method: "PUT", body: JSON.stringify(payload) },
    token,
  );
}

export function fetchAdminStats(token: string): Promise<AdminStats> {
  return request<AdminStats>("/admin/stats", {}, token);
}

export function fetchAdminUsers(
  token: string,
  params: {
    q?: string;
    verification_status?: VerificationStatus;
    is_admin?: boolean;
    limit?: number;
    offset?: number;
  } = {},
): Promise<AdminUserListResponse> {
  const search = new URLSearchParams();
  if (params.q) search.set("q", params.q);
  if (params.verification_status) {
    search.set("verification_status", params.verification_status);
  }
  if (params.is_admin !== undefined) {
    search.set("is_admin", String(params.is_admin));
  }
  if (params.limit !== undefined) search.set("limit", String(params.limit));
  if (params.offset !== undefined) search.set("offset", String(params.offset));
  const query = search.toString();
  const path = query ? `/admin/users?${query}` : "/admin/users";
  return request<AdminUserListResponse>(path, {}, token);
}

export function fetchAdminUser(
  token: string,
  userId: string,
): Promise<AdminUserDetail> {
  return request<AdminUserDetail>(`/admin/users/${userId}`, {}, token);
}

export function updateUserVerification(
  token: string,
  userId: string,
  payload: { verification_status: VerificationStatus; note?: string },
): Promise<AdminUserDetail> {
  return request<AdminUserDetail>(
    `/admin/users/${userId}/verification`,
    { method: "PATCH", body: JSON.stringify(payload) },
    token,
  );
}

export function updateUserRoles(
  token: string,
  userId: string,
  payload: { is_booker: boolean; is_act_owner: boolean },
): Promise<AdminUserDetail> {
  return request<AdminUserDetail>(
    `/admin/users/${userId}/roles`,
    { method: "PATCH", body: JSON.stringify(payload) },
    token,
  );
}

export function updateManagerVerification(
  token: string,
  userId: string,
  payload: { manager_verified: boolean; note?: string },
): Promise<AdminUserDetail> {
  return request<AdminUserDetail>(
    `/admin/users/${userId}/manager-verification`,
    { method: "PATCH", body: JSON.stringify(payload) },
    token,
  );
}

export function fetchActCategories(): Promise<ActCategory[]> {
  return request<ActCategory[]>("/act-categories");
}

export function fetchOfferings(params: {
  activity_type?: ActivityType;
  act_category_id?: string;
  min_price?: number;
  max_price?: number;
  genre?: Genre;
} = {}): Promise<OfferingSummary[]> {
  const search = new URLSearchParams();
  if (params.activity_type) search.set("activity_type", params.activity_type);
  if (params.act_category_id) search.set("act_category_id", params.act_category_id);
  if (params.min_price !== undefined) search.set("min_price", String(params.min_price));
  if (params.max_price !== undefined) search.set("max_price", String(params.max_price));
  if (params.genre) search.set("genre", params.genre);
  const query = search.toString();
  const path = query ? `/offerings?${query}` : "/offerings";
  return request<OfferingSummary[]>(path);
}

export function fetchOffering(id: string, token?: string | null): Promise<OfferingDetail> {
  return request<OfferingDetail>(`/offerings/${id}`, {}, token);
}

export function fetchOfferingOpenSlots(
  token: string,
  offeringId: string,
): Promise<AvailabilitySlot[]> {
  return request<AvailabilitySlot[]>(`/offerings/${offeringId}/slots`, {}, token);
}

export function fetchActOwnerActs(token: string): Promise<Act[]> {
  return request<Act[]>("/act-owner/acts", {}, token);
}

export function createActOwnerAct(
  token: string,
  payload: Omit<Act, "id" | "act_owner_id" | "created_at">,
): Promise<Act> {
  return request<Act>(
    "/act-owner/acts",
    { method: "POST", body: JSON.stringify(payload) },
    token,
  );
}

export function updateActOwnerAct(
  token: string,
  id: string,
  payload: Partial<Omit<Act, "id" | "act_owner_id" | "created_at">>,
): Promise<Act> {
  return request<Act>(
    `/act-owner/acts/${id}`,
    { method: "PATCH", body: JSON.stringify(payload) },
    token,
  );
}

export function fetchActOwnerOfferings(token: string): Promise<ActOwnerOffering[]> {
  return request<ActOwnerOffering[]>("/act-owner/offerings", {}, token);
}

export function createActOwnerOffering(
  token: string,
  payload: {
    act_id: string;
    activity_type: ActivityType;
    price: number;
    availability?: string;
    promoter_only_allowed?: boolean;
    active?: boolean;
    min_booker_experience?: number | null;
    max_venue_capacity?: number | null;
    sound_system_required?: boolean;
    equipment_provided?: string;
  },
): Promise<ActOwnerOffering> {
  return request<ActOwnerOffering>(
    "/act-owner/offerings",
    { method: "POST", body: JSON.stringify(payload) },
    token,
  );
}

export function updateActOwnerOffering(
  token: string,
  id: string,
  payload: Partial<{
    activity_type: ActivityType;
    price: number;
    availability: string;
    promoter_only_allowed: boolean;
    active: boolean;
    min_booker_experience: number | null;
    max_venue_capacity: number | null;
    sound_system_required: boolean;
    equipment_provided: string;
  }>,
): Promise<ActOwnerOffering> {
  return request<ActOwnerOffering>(
    `/act-owner/offerings/${id}`,
    { method: "PATCH", body: JSON.stringify(payload) },
    token,
  );
}

export function fetchAdminOfferings(
  token: string,
  params: { active?: boolean; act_owner_id?: string } = {},
): Promise<AdminOfferingListResponse> {
  const search = new URLSearchParams();
  if (params.active !== undefined) search.set("active", String(params.active));
  if (params.act_owner_id) search.set("act_owner_id", params.act_owner_id);
  const query = search.toString();
  const path = query ? `/admin/offerings?${query}` : "/admin/offerings";
  return request<AdminOfferingListResponse>(path, {}, token);
}

export function fetchAdminAudit(
  token: string,
  params: {
    actor_id?: string;
    target_user_id?: string;
    action?: string;
    limit?: number;
    offset?: number;
  } = {},
): Promise<AdminAuditLogListResponse> {
  const search = new URLSearchParams();
  if (params.actor_id) search.set("actor_id", params.actor_id);
  if (params.target_user_id) search.set("target_user_id", params.target_user_id);
  if (params.action) search.set("action", params.action);
  if (params.limit !== undefined) search.set("limit", String(params.limit));
  if (params.offset !== undefined) search.set("offset", String(params.offset));
  const query = search.toString();
  const path = query ? `/admin/audit?${query}` : "/admin/audit";
  return request<AdminAuditLogListResponse>(path, {}, token);
}

export function updateAdminOfferingActive(
  token: string,
  offeringId: string,
  active: boolean,
): Promise<AdminOfferingSummary> {
  return request<AdminOfferingSummary>(
    `/admin/offerings/${offeringId}`,
    { method: "PATCH", body: JSON.stringify({ active }) },
    token,
  );
}

export type PromoterConnectionStatus =
  | "pending_act_owner_confirm"
  | "pending_guardian"
  | "active"
  | "declined"
  | "revoked";

export interface PromoterConnection {
  id: string;
  act_owner_id: string;
  booker_id: string | null;
  invitee_email: string;
  status: PromoterConnectionStatus;
  invited_at: string;
  accepted_at: string | null;
  created_at: string;
}

export interface PromoterConnectionListResponse {
  items: PromoterConnection[];
}

export type GigStatus =
  | "pending_act_owner"
  | "pending_payment"
  | "approved"
  | "declined"
  | "cancelled"
  | "completed";

export type PaymentType = "paid" | "free";

export interface GigParticipant {
  gig_id: string;
  group_member_id: string | null;
  participant_display_name: string | null;
  booker_experience_warning?: string | null;
}

export interface GigRequest {
  id: string;
  offering_id: string;
  act_name: string;
  booker_id: string;
  booker_email: string;
  booker_verification_status: VerificationStatus;
  act_owner_id: string;
  act_owner_email: string;
  payment_type: PaymentType;
  status: GigStatus;
  scheduled_at: string | null;
  availability_slot_id?: string | null;
  note: string | null;
  requested_at: string;
  offering_price: string;
  activity_type: string;
  thread_id?: string | null;
  booker_experience_warning?: string | null;
  group_gig_id?: string | null;
  group_member_id?: string | null;
  participant_display_name?: string | null;
  is_group_gig?: boolean;
  group_party_size?: number | null;
  booker_group_name?: string | null;
  group_participants?: GigParticipant[] | null;
}

export interface GigListResponse {
  items: GigRequest[];
  total: number;
}

export function fetchActOwnerPromoterConnections(
  token: string,
): Promise<PromoterConnectionListResponse> {
  return request<PromoterConnectionListResponse>(
    "/act-owner/promoter-connections",
    {},
    token,
  );
}

export function createPromoterConnection(
  token: string,
  payload: { invitee_email: string },
): Promise<PromoterConnection> {
  return request<PromoterConnection>(
    "/act-owner/promoter-connections",
    { method: "POST", body: JSON.stringify(payload) },
    token,
  );
}

export function cancelPromoterConnection(
  token: string,
  connectionId: string,
): Promise<PromoterConnection> {
  return request<PromoterConnection>(
    `/act-owner/promoter-connections/${connectionId}`,
    { method: "PATCH", body: JSON.stringify({ status: "revoked" }) },
    token,
  );
}

export function fetchBookerPromoterConnections(
  token: string,
): Promise<PromoterConnectionListResponse> {
  return request<PromoterConnectionListResponse>(
    "/booker/promoter-connections",
    {},
    token,
  );
}

export function respondPromoterConnection(
  token: string,
  connectionId: string,
  status: "accepted" | "declined",
): Promise<PromoterConnection> {
  return request<PromoterConnection>(
    `/booker/promoter-connections/${connectionId}/respond`,
    { method: "PATCH", body: JSON.stringify({ status }) },
    token,
  );
}

export function createGig(
  token: string,
  payload: {
    offering_id: string;
    availability_slot_id?: string;
    note?: string;
    group_member_ids?: string[];
  },
): Promise<GigRequest> {
  return request<GigRequest>(
    "/gigs",
    { method: "POST", body: JSON.stringify(payload) },
    token,
  );
}

export function fetchGigs(
  token: string,
  role: "booker" | "act_owner" = "booker",
): Promise<GigListResponse> {
  return request<GigListResponse>(`/gigs?role=${role}`, {}, token);
}

export function updateGigStatus(
  token: string,
  gigId: string,
  status: "approved" | "declined" | "cancelled" | "completed",
): Promise<GigRequest> {
  return request<GigRequest>(
    `/gigs/${gigId}`,
    { method: "PATCH", body: JSON.stringify({ status }) },
    token,
  );
}

export function fetchAdminGigs(
  token: string,
  params: { limit?: number; offset?: number } = {},
): Promise<GigListResponse> {
  const search = new URLSearchParams();
  if (params.limit !== undefined) search.set("limit", String(params.limit));
  if (params.offset !== undefined) search.set("offset", String(params.offset));
  const query = search.toString();
  const path = query ? `/admin/gigs?${query}` : "/admin/gigs";
  return request<GigListResponse>(path, {}, token);
}

export interface PublicAct {
  act_name: string;
  act_category: string;
  act_type: string | null;
  years_active: number | null;
  photo_urls: string[];
  activity_type: ActivityType;
  price: string | null;
  display_location: string;
  public_lat: number;
  public_lng: number;
  act_owner_first_name: string;
  act_owner_last_initial: string;
  act_owner_verified: boolean;
  act_owner_manager_verified: boolean;
  act_owner_member_since: string;
  review_count: number;
  review_average: number | null;
  genres: Genre[];
  slug: string;
  active: boolean;
  min_booker_experience: number | null;
  min_booker_experience_label: string | null;
  max_venue_capacity: number | null;
  sound_system_required: boolean;
  equipment_provided: string;
  equipment_provided_label: string;
}

export interface PublicInvitePreview {
  act_owner_first_name: string;
  act_owner_verified: boolean;
  act_names: string[];
  token_valid: boolean;
  expired: boolean;
  revoked: boolean;
}

export interface InviteToken {
  id: string;
  token: string;
  act_id: string | null;
  max_uses: number;
  use_count: number;
  expires_at: string;
  revoked_at: string | null;
  created_at: string;
  share_url: string;
}

export interface InviteTokenListResponse {
  items: InviteToken[];
}

export interface AdminPlatformFlag {
  id: string;
  user_id: string;
  user_email: string;
  flag_type: string;
  details: Record<string, unknown> | null;
  created_at: string;
  resolved_at: string | null;
}

export interface AdminPlatformFlagListResponse {
  items: AdminPlatformFlag[];
  total: number;
}

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export function publicActUrl(slug: string): string {
  return `${SITE_URL}/a/${slug}`;
}

export function fetchPublicAct(slug: string): Promise<PublicAct> {
  return request<PublicAct>(`/public/acts/${slug}`);
}

export function fetchPublicInvite(token: string): Promise<PublicInvitePreview> {
  return request<PublicInvitePreview>(`/public/invites/${token}`);
}

export function createInviteToken(
  token: string,
  payload: { act_id?: string; max_uses?: number; expires_in_days?: number } = {},
): Promise<InviteToken> {
  return request<InviteToken>(
    "/invites/tokens",
    { method: "POST", body: JSON.stringify(payload) },
    token,
  );
}

export function fetchInviteTokens(token: string): Promise<InviteTokenListResponse> {
  return request<InviteTokenListResponse>("/invites/tokens", {}, token);
}

export function revokeInviteToken(token: string, tokenId: string): Promise<void> {
  return request<void>(`/invites/tokens/${tokenId}`, { method: "DELETE" }, token);
}

export function redeemInviteToken(
  token: string,
  inviteToken: string,
): Promise<{ promoter_connection_id: string; status: string }> {
  return request(`/invites/tokens/${inviteToken}/redeem`, { method: "POST" }, token);
}

export function confirmPromoterConnection(
  token: string,
  connectionId: string,
  action: "confirm" | "decline",
): Promise<{ status: string }> {
  return request(
    `/invites/${connectionId}/confirm`,
    { method: "POST", body: JSON.stringify({ action }) },
    token,
  );
}

export function guardianApproveInvite(
  token: string,
  connectionId: string,
): Promise<{ status: string }> {
  return request(`/invites/${connectionId}/guardian-approve`, { method: "POST" }, token);
}

export function createGigReview(
  token: string,
  gigId: string,
  payload: { rating: number; body?: string },
): Promise<{ id: string; rating: number }> {
  return request(
    `/gigs/${gigId}/reviews`,
    { method: "POST", body: JSON.stringify(payload) },
    token,
  );
}

export function fetchAdminFlags(token: string): Promise<AdminPlatformFlagListResponse> {
  return request<AdminPlatformFlagListResponse>("/admin/flags", {}, token);
}

export async function uploadOfferingPhoto(
  token: string,
  offeringId: string,
  file: File,
): Promise<{ id: string; url: string; thumbnail_url: string }> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${API_URL}/act-owner/offerings/${offeringId}/photos`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
  if (!response.ok) {
    throw new ApiError(await parseError(response), response.status);
  }
  return (await response.json()) as { id: string; url: string; thumbnail_url: string };
}

export function logClientEvent(
  payload: {
    event_type: string;
    src?: string;
    act_slug?: string;
    invite_token?: string;
  },
  token?: string | null,
): Promise<void> {
  return request<void>(
    "/events",
    { method: "POST", body: JSON.stringify(payload) },
    token,
  );
}

export interface AvailabilitySlot {
  id: string;
  offering_id: string;
  start_at: string;
  end_at: string;
  status: string;
  capacity: number;
  created_at: string;
}

export interface CalendarWeatherDay {
  date: string;
  temp_max_f: number | null;
  temp_min_f: number | null;
  precip_probability_max: number | null;
  wind_speed_max_mph: number | null;
  weather_code: number | null;
  gig_suitability: "good" | "caution" | "poor";
  summary: string;
}

export interface CalendarDaySummary {
  date: string;
  open_slot_count: number;
  my_gig_count: number;
  weather: CalendarWeatherDay | null;
}

export interface OpenSlotSummary {
  id: string;
  offering_id: string;
  slug: string;
  act_name: string;
  activity_type: ActivityType;
  price: string;
  display_location: string;
  start_at: string;
  end_at: string;
}

export interface CalendarResponse {
  days: CalendarDaySummary[];
  open_slots: OpenSlotSummary[];
  my_gigs: GigRequest[];
  weather_error: string | null;
}

export function fetchCalendar(
  token: string,
  params: {
    from: string;
    to: string;
    lat?: number;
    lng?: number;
    radius_km?: number;
    include_open_slots?: boolean;
  },
): Promise<CalendarResponse> {
  const search = new URLSearchParams();
  search.set("from", params.from);
  search.set("to", params.to);
  if (params.lat !== undefined) search.set("lat", String(params.lat));
  if (params.lng !== undefined) search.set("lng", String(params.lng));
  if (params.radius_km !== undefined) search.set("radius_km", String(params.radius_km));
  if (params.include_open_slots !== undefined) {
    search.set("include_open_slots", String(params.include_open_slots));
  }
  return request<CalendarResponse>(`/calendar?${search.toString()}`, {}, token);
}

export function fetchActOwnerOfferingSlots(
  token: string,
  offeringId: string,
  params: { from?: string; to?: string } = {},
): Promise<AvailabilitySlot[]> {
  const search = new URLSearchParams();
  if (params.from) search.set("from", params.from);
  if (params.to) search.set("to", params.to);
  const query = search.toString();
  const path = query
    ? `/act-owner/offerings/${offeringId}/slots?${query}`
    : `/act-owner/offerings/${offeringId}/slots`;
  return request<AvailabilitySlot[]>(path, {}, token);
}

export function createActOwnerOfferingSlot(
  token: string,
  offeringId: string,
  payload: { start_at: string; end_at: string; capacity?: number },
): Promise<AvailabilitySlot> {
  return request<AvailabilitySlot>(
    `/act-owner/offerings/${offeringId}/slots`,
    { method: "POST", body: JSON.stringify(payload) },
    token,
  );
}

export function updateActOwnerOfferingSlot(
  token: string,
  offeringId: string,
  slotId: string,
  payload: { start_at?: string; end_at?: string; status?: "open" | "blocked" },
): Promise<AvailabilitySlot> {
  return request<AvailabilitySlot>(
    `/act-owner/offerings/${offeringId}/slots/${slotId}`,
    { method: "PATCH", body: JSON.stringify(payload) },
    token,
  );
}

export function deleteActOwnerOfferingSlot(
  token: string,
  offeringId: string,
  slotId: string,
): Promise<void> {
  return request<void>(
    `/act-owner/offerings/${offeringId}/slots/${slotId}`,
    { method: "DELETE" },
    token,
  );
}

export interface ThreadMessage {
  id: string;
  thread_id: string;
  sender_id: string;
  body: string;
  sent_at: string;
}

export interface ThreadMessageListResponse {
  items: ThreadMessage[];
  total: number;
}

export function fetchThreadMessages(
  token: string,
  threadId: string,
): Promise<ThreadMessageListResponse> {
  return request<ThreadMessageListResponse>(`/threads/${threadId}/messages`, {}, token);
}

export function postThreadMessage(
  token: string,
  threadId: string,
  body: string,
): Promise<ThreadMessage> {
  return request<ThreadMessage>(
    `/threads/${threadId}/messages`,
    { method: "POST", body: JSON.stringify({ body }) },
    token,
  );
}
