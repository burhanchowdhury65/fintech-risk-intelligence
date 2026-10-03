/** Frontend convention (not part of the API contract). Set in .env.local. */
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

/** Mock mode is ON unless NEXT_PUBLIC_USE_MOCK_API=false. Day 3 switches to the real API. */
export const USE_MOCK_API = process.env.NEXT_PUBLIC_USE_MOCK_API !== "false";
