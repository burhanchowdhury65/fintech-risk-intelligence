import type { AnalyzeRequest, FieldErrors, FieldName } from "@/lib/types/api";

export interface FormValues {
  transaction_amount: string;
  transaction_time: string;
  transaction_type: string;
  merchant_category: string;
  distance_from_home: string;
  customer_latitude: string;
  customer_longitude: string;
  merchant_latitude: string;
  merchant_longitude: string;
}

export const EMPTY_FORM: FormValues = {
  transaction_amount: "",
  transaction_time: "",
  transaction_type: "",
  merchant_category: "",
  distance_from_home: "",
  customer_latitude: "",
  customer_longitude: "",
  merchant_latitude: "",
  merchant_longitude: "",
};

export const FIELD_LABELS: Record<FieldName, string> = {
  transaction_amount: "Transaction amount",
  transaction_time: "Transaction time",
  transaction_type: "Transaction type",
  merchant_category: "Merchant category",
  distance_from_home: "Distance from home",
  customer_latitude: "Customer latitude",
  customer_longitude: "Customer longitude",
  merchant_latitude: "Merchant latitude",
  merchant_longitude: "Merchant longitude",
};

/** Rules confirmed by Person B (Pydantic schema): amount > 0, distance >= 0, time is a valid datetime. */
export function validate(v: FormValues): FieldErrors {
  const e: FieldErrors = {};
  const amount = Number(v.transaction_amount);
  if (v.transaction_amount.trim() === "" || !Number.isFinite(amount)) e.transaction_amount = "Enter the amount as a number, for example 128.50.";
  else if (amount <= 0) e.transaction_amount = "Amount must be greater than 0.";
  if (!v.transaction_time) e.transaction_time = "Choose the date and time of the transaction.";
  if (!v.transaction_type.trim()) e.transaction_type = "Enter a transaction type, for example purchase.";
  if (!v.merchant_category) e.merchant_category = "Choose a merchant category.";
  if (v.distance_from_home.trim() !== "") {
    const d = Number(v.distance_from_home);
    if (!Number.isFinite(d)) e.distance_from_home = "Enter the distance as a number, or leave it empty.";
    else if (d < 0) e.distance_from_home = "Distance cannot be negative. Enter 0 or more.";
  }
  const coordinates = [
    ["customer_latitude", v.customer_latitude, -90, 90],
    ["customer_longitude", v.customer_longitude, -180, 180],
    ["merchant_latitude", v.merchant_latitude, -90, 90],
    ["merchant_longitude", v.merchant_longitude, -180, 180],
  ] as const;

  const hasAnyCoordinate = coordinates.some(([, value]) => value.trim() !== "");

  if (hasAnyCoordinate) {
    for (const [field, value, min, max] of coordinates) {
      if (value.trim() === "") {
        e[field] = "Enter all four coordinates.";
        continue;
      }

      const n = Number(value);
      if (!Number.isFinite(n) || n < min || n > max) {
        e[field] = `Enter a valid value between ${min} and ${max}.`;
      }
    }
  }

  return e;
}

export function toAnalyzeRequest(v: FormValues): AnalyzeRequest {
  const time = v.transaction_time.length === 16 ? `${v.transaction_time}:00` : v.transaction_time;
  return {
    transaction_amount: Number(v.transaction_amount),
    transaction_type: v.transaction_type.trim(),
    merchant_category: v.merchant_category.trim(),
    transaction_time: time,
    distance_from_home: v.distance_from_home.trim() === "" ? null : Number(v.distance_from_home),
    location:
      v.customer_latitude.trim() !== "" &&
      v.customer_longitude.trim() !== "" &&
      v.merchant_latitude.trim() !== "" &&
      v.merchant_longitude.trim() !== ""
        ? {
            customer_lat: Number(v.customer_latitude),
            customer_long: Number(v.customer_longitude),
            merchant_lat: Number(v.merchant_latitude),
            merchant_long: Number(v.merchant_longitude),
          }
        : null,
  };
}

export function fromRequest(r: AnalyzeRequest): FormValues {
  const location = r.location;

  return {
    transaction_amount: String(r.transaction_amount),
    transaction_time: r.transaction_time.slice(0, 16),
    transaction_type: r.transaction_type,
    merchant_category: r.merchant_category,
    distance_from_home: r.distance_from_home == null ? "" : String(r.distance_from_home),
    customer_latitude:
      typeof location === "object" && location !== null && "customer_lat" in location
        ? String(location.customer_lat)
        : "",
    customer_longitude:
      typeof location === "object" && location !== null && "customer_long" in location
        ? String(location.customer_long)
        : "",
    merchant_latitude:
      typeof location === "object" && location !== null && "merchant_lat" in location
        ? String(location.merchant_lat)
        : "",
    merchant_longitude:
      typeof location === "object" && location !== null && "merchant_long" in location
        ? String(location.merchant_long)
        : "",
  };
}
