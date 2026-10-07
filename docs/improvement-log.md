# Fintech Risk Intelligence — Improvement Log

This document records the major improvements made after the initial prototype evaluation. The improvements focus on model performance, AI reasoning quality, geographic risk intelligence, and demo reliability.

---

# 1. Fraud Risk Threshold Optimization

## Problem

The initial fraud-risk decision threshold achieved very high recall, but it also produced a large number of false positives.

On the held-out test set, the original threshold produced:

| Metric | Original |
|---|---:|
| Precision | 22.08% |
| Recall | 95.15% |
| F1 Score | 0.358 |
| False Positives | 7,203 |
| False Negatives | 104 |

A high number of false positives can increase unnecessary manual reviews and create additional customer friction in a real fraud-risk workflow.

## Improvement

The fraud decision threshold was optimized using validation data and then evaluated on the held-out test set.

The selected threshold was changed to:

**0.60**

This provides a better precision-recall trade-off while maintaining strong fraud detection coverage.

## Held-out Test Results

| Metric | Original Threshold | Optimized Threshold (0.60) |
|---|---:|---:|
| Precision | 22.08% | **41.58%** |
| Recall | 95.15% | **90.54%** |
| F1 Score | 0.358 | **0.570** |
| False Positives | 7,203 | **2,729** |
| False Negatives | 104 | 203 |

## Measured Improvement

- Precision improved by **19.50 percentage points**.
- False positives decreased from **7,203 to 2,729**.
- This represents approximately a **62% reduction in false positives**.
- Recall remained above **90%** at **90.54%**.
- F1 score improved from **0.358 to 0.570**.
- PR-AUC and ROC-AUC remain unchanged because threshold selection affects the final classification decision rather than the underlying ranking performance.

## Business Interpretation

The improvement is intended to reduce unnecessary alerts while maintaining strong fraud detection coverage.

The 62% figure refers specifically to the reduction in **false-positive predictions on the held-out test set**. It should not be interpreted as a 62% reduction in actual fraud losses.

---

# 2. Model-Grounded ARIA Improvements

## Problem

ARIA previously focused primarily on intent understanding, routing, and generating explanations. The reasoning layer needed stronger grounding in verified ML outputs.

## Improvement

ARIA's reasoning rules were strengthened so that explanations are based on verified analysis results rather than unsupported assumptions.

ARIA is now instructed to:

- Separate verified ML evidence from ARIA's own interpretation.
- Base reasoning only on the verified analysis result.
- Identify the most important available model risk factors.
- Explain what those factors mean in the context of the transaction.
- Clearly distinguish model risk assessment from confirmed fraud.
- Provide practical recommendations such as manual review, additional verification, or no immediate action.
- Avoid inventing customer history, transaction history, financial policies, external evidence, or unsupported facts.

## Source of Truth

The ML/Risk Node remains authoritative for:

- Risk score
- Risk status
- Fraud prediction
- Model factors
- Model version
- Counterfactual results

ARIA interprets these verified outputs and communicates them in a human-readable form.

## Safety Principle

A high-risk model prediction does **not** mean that fraud has been confirmed.

ARIA should communicate the result as a risk assessment and provide an evidence-based recommendation.

For example:

> "The transaction has a high model risk score and should be reviewed."

Instead of:

> "This transaction is definitely fraudulent."

This distinction helps keep the AI explanation aligned with the actual model output.

---

# 3. Geographic Risk Intelligence

## Problem

Geographic transaction distance is an important risk signal, but relying only on manually entered distance values is less consistent and less practical.

## Improvement

The system now accepts structured geographic coordinates for both the customer and merchant:

```text
Customer latitude
Customer longitude

Merchant latitude
Merchant longitude

The location data is passed through the existing API contract.
The ML inference layer then calculates the geographic distance using the Haversine formula.
Customer Coordinates
        +
Merchant Coordinates
        ↓
Haversine Distance Calculation
        ↓
distance_from_home_km
        ↓
Existing ML Model
        ↓
Risk Score + Model Factors
        ↓
ARIA Explanation

Why Haversine?
Latitude and longitude represent positions on the Earth's surface.
The Haversine formula provides a practical way to calculate the great-circle distance between two geographic coordinates.
This allows the system to derive geographic distance automatically instead of depending entirely on manually entered distance values.
Model Integration
Geographic distance was already part of the model's feature representation as:
distance_from_home_km

Therefore, this improvement does not introduce a new model feature and does not require model retraining.
The improvement changes how the geographic feature is supplied during inference.
Input Validation
The frontend validates:
- Latitude between -90 and 90
- Longitude between -180 and 180
- If any coordinate is entered, all four coordinates must be provided.
Backward Compatibility
The existing distance_from_home value can still act as a fallback when coordinates are not available.
When valid coordinates are supplied, the system prioritizes the calculated geographic distance.
Interpretation
Geographic distance is treated as a risk signal, not proof of fraud.
For example, a transaction occurring far from the customer's location may increase risk, but the final risk assessment still depends on the complete set of model features and the model output.
4. Demo Scenario Improvements
The demo scenarios were updated to include structured customer and merchant coordinates.
Example:
{
  "customer_lat": 23.7104,
  "customer_long": 90.4074,
  "merchant_lat": 22.3384,
  "merchant_long": 91.8317
}

This allows the demo to demonstrate geographic-risk processing using structured location data.
Different demo scenarios can represent:
- Nearby customer and merchant locations
- Moderately distant locations
- Large geographic separation
This makes the geographic-risk component easier to demonstrate during evaluation.
5. End-to-End Improved Workflow
The improved system follows:
Transaction
    ↓
Input Validation
    ↓
Feature Preparation
    ↓
Geographic Distance Calculation
    ↓
Fraud/Risk ML Model
    ↓
Optimized Risk Threshold
    ↓
Risk Score + Model Factors
    ↓
Counterfactual Analysis
    ↓
ARIA Model-Grounded Explanation
    ↓
Recommended Operational Action

Core Product Flow
Detect → Explain → Simulate → Decide
Detect
The ML model evaluates the transaction and produces a risk assessment.
Explain
ARIA explains the verified model evidence in human-readable language.
Simulate
Counterfactual analysis explores tested feature changes that may alter the model prediction.
Decide
The system provides an evidence-based operational recommendation such as manual review, additional verification, or no immediate action.
6. Responsible AI Considerations
The system is designed as a decision-support prototype rather than an autonomous fraud-decision system.
Important principles include:
- Model risk is not treated as confirmed fraud.
- ARIA should not invent missing evidence.
- Geographic distance is not used as a standalone fraud decision.
- Counterfactual results are illustrative and depend on the tested feature range.
- ML outputs remain the source of truth for risk-related values.
- Human review remains important for high-risk decisions.
7. Current Limitations
The current prototype has several limitations that would need to be addressed before production deployment.
Dataset
The current evaluation is based on a public fraud-detection dataset rather than live data from a financial institution.
Business Impact
Actual reductions in:
- fraud losses
- manual review cost
- customer complaints
- customer friction
have not yet been measured in a production financial environment.
The current quantitative evidence is based on model evaluation metrics.
Geographic Signal
Geographic distance is only one risk signal. A large distance does not independently prove fraudulent activity.
Counterfactuals
Counterfactual results are illustrative and depend on the feature values and tested ranges available to the system.
Production Security
A production financial deployment would require stronger:
- authentication and authorization
- encryption
- privacy controls
- data-retention policies
- threat modelling
- security testing
- fairness monitoring
- compliance controls
- operational monitoring
8. Improvement Summary
Area	Improvement	Measured / Expected Result
Model Performance	Threshold optimization	Precision: 22.08% → 41.58%
False Positives	Threshold optimization	~62% reduction
Recall	Threshold optimization	Maintained at 90.54%
F1 Score	Threshold optimization	0.358 → 0.570
AI Reasoning	Model-grounded ARIA	More evidence-based explanations
Geographic Intelligence	Coordinate-based distance	Automatic geographic feature calculation
Demo Quality	Structured location scenarios	More realistic geographic-risk demonstrations
Decision Support	Detect → Explain → Simulate → Decide	More actionable risk workflow


Conclusion
The improvements strengthen the prototype in three key dimensions:
1. Better model decision quality through threshold optimization.
2. More reliable AI reasoning through model-grounded ARIA behavior.
3. More practical geographic intelligence through automatic coordinate-based distance calculation.
Together, these changes move the system from a basic fraud-risk prototype toward a more practical, explainable, and decision-oriented financial risk intelligence platform.