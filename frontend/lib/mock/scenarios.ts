/**
 * MOCK DATA. The normal, flagged and cached inputs and responses are the exact demo list confirmed by Person B
 * (real model outputs, Day 6). Inputs for the service-error and invalid demos are invented.
 * The CACHED source_mode is a mock assumption: source_mode is still TBD in the real contract.
 */
import type { AnalyzeRequest, AnalyzeResponse, ApiErrorCode } from "@/lib/types/api";

export type MockOutcome =
  | { kind: "response"; response: AnalyzeResponse }
  | { kind: "error"; code: ApiErrorCode; message: string; requestId: string };

export interface DemoScenario {
  id: string;
  label: string;
  hint: string;
  input: AnalyzeRequest;
  /** Needs mock mode: a live backend would not produce this outcome. */
  mockOnly?: boolean;
  /** Undefined = the form is invalid, so the request never leaves the browser. */
  outcome?: MockOutcome;
}

export const MOCK_MODEL_VERSION = "histgb-candidate-day3-v1";

export const DEMO_SCENARIOS: DemoScenario[] = [
  {
    id: "normal",
    label: "Demo: Normal Transaction",
    hint: "Small grocery purchase",
    input: { transaction_amount: 45, transaction_type: "purchase", merchant_category: "grocery_pos", transaction_time: "2026-09-28T14:30:00", distance_from_home: null, location: { customer_lat: 23.8103, customer_long: 90.4125, merchant_lat: 23.8125, merchant_long: 90.4150 } },
    outcome: {
      kind: "response",
      response: { request_id: "MOCK-REQ-001", is_fraud: false, risk_score: 0, risk_status: "low", model_factors: [], model_version: MOCK_MODEL_VERSION },
    },
  },
  {
    id: "flagged",
    label: "Demo: Flagged Transaction",
    hint: "Large, far away, late at night",
    input: { transaction_amount: 890, transaction_type: "purchase", merchant_category: "shopping_net", transaction_time: "2026-09-28T03:15:00", distance_from_home: 240, location: { customer_lat: 23.8103, customer_long: 90.4125, merchant_lat: 21.4272, merchant_long: 92.0058 } },
    outcome: {
      kind: "response",
      response: {
        request_id: "MOCK-REQ-002", is_fraud: true, risk_score: 99, risk_status: "high", model_version: MOCK_MODEL_VERSION,
        model_factors: ["Transaction amount is unusually high", "Transaction location is far from customer's home", "Transaction occurred at an unusual hour"],
        // Copy of the real counterfactual Person B confirmed for this exact input (Day 7). Shown with a "Sample data" badge in mock mode.
        counterfactual: { found: true, changed_feature: "amt", changed_feature_label: "transaction amount", original_value: 890, suggested_value: 623, new_risk_score: 67, new_risk_status: "medium", reason: "If the transaction amount had been 623.00 instead of 890.00, the risk score would have been 67 instead of the original score." },
      },
    },
  },
  {
    id: "cached",
    label: "Demo: Cached Demo",
    hint: "Saved result for one fixed input",
    input: { transaction_amount: 128.5, transaction_type: "purchase", merchant_category: "grocery_pos", transaction_time: "2026-09-28T14:30:00", distance_from_home: 3.2, location: { customer_lat: 23.8103, customer_long: 90.4125, merchant_lat: 23.8390, merchant_long: 90.3980 } },
    outcome: {
      kind: "response",
      response: { request_id: "MOCK-REQ-003", is_fraud: false, risk_score: 0, risk_status: "low", model_factors: [], model_version: MOCK_MODEL_VERSION, source_mode: "CACHED" },
    },
  },
  {
    id: "unavailable",
    mockOnly: true,
    label: "Demo: Service Error",
    hint: "Risk service is down",
    input: { transaction_amount: 75, transaction_type: "purchase", merchant_category: "gas_transport", transaction_time: "2026-09-26T10:05:00", distance_from_home: 8, location: { customer_lat: 23.8103, customer_long: 90.4125, merchant_lat: 23.8750, merchant_long: 90.4050 } },
    outcome: { kind: "error", code: "ML_NODE_UNAVAILABLE", message: "ML/Risk node is currently unavailable", requestId: "MOCK-REQ-004" },
  },
  {
    id: "invalid",
    label: "Demo: Invalid Input",
    hint: "Negative amount",
    input: { transaction_amount: -50, transaction_type: "purchase", merchant_category: "grocery_pos", transaction_time: "2026-09-26T14:30:00", distance_from_home: 3.2, location: { customer_lat: 23.8103, customer_long: 90.4125, merchant_lat: 23.8390, merchant_long: 90.3980 } },
  },
];
