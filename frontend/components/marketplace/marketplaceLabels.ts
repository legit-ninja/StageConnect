import { ActivityType, Genre, VerificationStatus } from "@/lib/api";

export const GENRE_OPTIONS: Genre[] = ["jazz", "rock", "pop", "country", "classical"];

const GENRE_LABEL: Record<Genre, string> = {
  jazz: "Jazz",
  rock: "Rock",
  pop: "Pop",
  country: "Country",
  classical: "Classical",
};

const ACTIVITY_LABEL: Record<ActivityType, string> = {
  private_gig: "Private gig",
  corporate: "Corporate event",
  wedding: "Wedding",
  festival: "Festival",
};

const PROMOTER_STATUS_LABEL: Record<string, string> = {
  pending_act_owner_confirm: "Awaiting booker",
  pending_guardian: "Awaiting guardian",
  active: "Active",
  declined: "Declined",
  revoked: "Revoked",
};

const GIG_STATUS_LABEL: Record<string, string> = {
  pending_act_owner: "Awaiting act owner",
  pending_payment: "Payment pending",
  approved: "Approved",
  declined: "Declined",
  cancelled: "Cancelled",
  completed: "Completed",
};

export function activityTypeLabel(type: ActivityType | string): string {
  return ACTIVITY_LABEL[type as ActivityType] ?? type.replace(/_/g, " ");
}

export function gigStatusLabel(status: string): string {
  return GIG_STATUS_LABEL[status] ?? status.replace(/_/g, " ");
}

export function promoterConnectionStatusLabel(status: string): string {
  return PROMOTER_STATUS_LABEL[status] ?? status.replace(/_/g, " ");
}

export function verificationLabel(status: VerificationStatus): string {
  const labels: Record<VerificationStatus, string> = {
    unverified: "Unverified",
    pending: "Pending review",
    verified: "Verified",
    rejected: "Rejected",
  };
  return labels[status];
}

export function genreLabel(genre: Genre | string): string {
  return GENRE_LABEL[genre as Genre] ?? genre.replace(/_/g, " ");
}
