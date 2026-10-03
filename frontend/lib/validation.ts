import type { AnalyzeRequest, FieldErrors, FieldName } from "@/lib/types/api";

export interface FormValues {
  transaction_amount: string;
  transaction_time: string;
  transaction_type: string;
  merchant_category: string;
  distance_from_home: string;
}

export const EMPTY_FORM: FormValues = {
  transaction_amount: "",
  transaction_time: "",
  transaction_type: "",
  merchant_category: "",
  distance_from_home: "",
};

export const FIELD_LABELS: Record<FieldName, string> = {
  transaction_amount: "Transaction amount",
  transaction_time: "Transaction time",
  transaction_type: "Transaction type",
  merchant_category: "Merchant category",
  distance_from_home: "Distance from home",
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
    location: null,
  };
}

export function fromRequest(r: AnalyzeRequest): FormValues {
  return {
    transaction_amount: String(r.transaction_amount),
    transaction_time: r.transaction_time.slice(0, 16),
    transaction_type: r.transaction_type,
    merchant_category: r.merchant_category,
    distance_from_home: r.distance_from_home == null ? "" : String(r.distance_from_home),
  };
}
