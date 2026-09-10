import type { EvidenceResult } from "@/types/forensics";

const apiUrl = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiUrl}${path}`, init);
  } catch {
    throw new Error("The DFIR backend is unavailable. Confirm it is running and NEXT_PUBLIC_API_URL is correct.");
  }
  if (!response.ok) {
    let message = `Request failed (${response.status}).`;
    try { message = (await response.json()).detail ?? message; } catch { /* non-JSON error */ }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export const dfirApi = {
  ingestEvidence(file: File, liveHunt: boolean) {
    const form = new FormData();
    form.append("file", file);
    form.append("live_hunt", String(liveHunt));
    return request<EvidenceResult>("/api/v1/upload", { method: "POST", body: form });
  },
  certificateUrl(caseId: string) {
    return `${apiUrl}/api/v1/cases/${encodeURIComponent(caseId)}/pdf`;
  },
};
