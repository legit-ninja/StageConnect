import { AdminUserSummary } from "@/lib/api";

const OAUTH_LABEL: Record<string, string> = {
  google: "Google",
  facebook: "Facebook",
};

const ACTIVITY_LABEL: Record<string, string> = {
  private_gig: "Private gig",
  corporate: "Corporate event",
  wedding: "Wedding",
  festival: "Festival",
};

export function formatRoles(
  user: Pick<
    AdminUserSummary,
    | "is_booker"
    | "is_act_owner"
    | "is_act_manager"
    | "is_booking_coordinator"
    | "manager_verified"
  >,
): string {
  const roles: string[] = [];
  if (user.is_booker) roles.push("Booker");
  if (user.is_act_owner) roles.push("Act Owner");
  if (user.is_act_manager) roles.push("Act manager");
  if (user.is_booking_coordinator) roles.push("Booking coordinator");
  if (user.manager_verified) roles.push("Verified manager");
  return roles.length > 0 ? roles.join(" · ") : "—";
}

export function formatManagerSelfReport(
  user: Pick<AdminUserSummary, "is_act_manager" | "is_booking_coordinator" | "manager_verified">,
): string {
  const parts: string[] = [];
  if (user.is_act_manager) parts.push("Act manager (self-reported)");
  if (user.is_booking_coordinator) parts.push("Booking coordinator (self-reported)");
  if (user.manager_verified) parts.push("Verified manager");
  return parts.length > 0 ? parts.join(" · ") : "—";
}

export function formatAuthMethod(oauthProviders: string[]): string {
  if (oauthProviders.length === 0) {
    return "Password";
  }
  return oauthProviders
    .map((provider) => OAUTH_LABEL[provider] ?? provider)
    .join(", ");
}

export function activityTypeLabel(activityType: string): string {
  return ACTIVITY_LABEL[activityType] ?? activityType.replace(/_/g, " ");
}

export function auditActionLabel(action: string): string {
  const labels: Record<string, string> = {
    verification_status_changed: "Verification changed",
    user_roles_changed: "Roles changed",
    offering_deactivated: "Offering deactivated",
    offering_reactivated: "Offering reactivated",
  };
  return labels[action] ?? action.replace(/_/g, " ");
}
