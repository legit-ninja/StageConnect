import { ImageResponse } from "next/og";

import { activityTypeLabel } from "@/components/marketplace/marketplaceLabels";
import type { PublicAct } from "@/lib/api";
import { getServerApiUrl } from "@/lib/server-api";

export const runtime = "edge";

async function loadOffering(slug: string): Promise<PublicAct | null> {
  const response = await fetch(`${getServerApiUrl()}/public/acts/${slug}`, {
    next: { revalidate: 300 },
  });
  if (!response.ok) return null;
  return (await response.json()) as PublicAct;
}

export async function GET(
  _request: Request,
  context: { params: Promise<{ slug: string }> },
) {
  const { slug } = await context.params;
  const offering = await loadOffering(slug);

  if (!offering) {
    return new ImageResponse(
      (
        <div
          style={{
            width: "100%",
            height: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "#0a0a0c",
            color: "#f0ece4",
            fontSize: 48,
          }}
        >
          StageConnect
        </div>
      ),
      { width: 1200, height: 630 },
    );
  }

  const activity = activityTypeLabel(offering.activity_type);
  const photo = offering.photo_urls[0];

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          background: "#0a0a0c",
          color: "#f0ece4",
          fontFamily: "system-ui, sans-serif",
        }}
      >
        {photo ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={photo}
            alt=""
            style={{ width: 420, height: "100%", objectFit: "cover" }}
          />
        ) : (
          <div style={{ width: 420, height: "100%", background: "#2a3441" }} />
        )}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            padding: 48,
            gap: 16,
          }}
        >
          <div style={{ fontSize: 52, fontWeight: 700 }}>{offering.act_name}</div>
          <div style={{ fontSize: 28, color: "#c9d1d9" }}>
            {activity} · {offering.display_location}
          </div>
          {offering.act_owner_verified ? (
            <div
              style={{
                marginTop: 8,
                padding: "8px 16px",
                background: "#1f6f4a",
                borderRadius: 8,
                fontSize: 22,
                alignSelf: "flex-start",
              }}
            >
              Verified act owner
            </div>
          ) : null}
          <div style={{ marginTop: "auto", fontSize: 24, color: "#8b949e" }}>
            StageConnect
          </div>
        </div>
      </div>
    ),
    {
      width: 1200,
      height: 630,
      headers: {
        "Cache-Control": "public, max-age=3600, stale-while-revalidate=86400",
      },
    },
  );
}
