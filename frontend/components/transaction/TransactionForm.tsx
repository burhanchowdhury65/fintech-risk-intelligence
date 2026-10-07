import { Button } from "@/components/ui/Button";
import { MERCHANT_CATEGORIES, categoryLabel } from "@/lib/constants";
import { USE_MOCK_API } from "@/lib/config";
import { DEMO_SCENARIOS, type DemoScenario } from "@/lib/mock/scenarios";
import { FIELD_LABELS, type FormValues } from "@/lib/validation";
import type { FieldErrors, FieldName } from "@/lib/types/api";

const base = "mt-1 block w-full min-h-11 rounded-control border bg-surface px-3 text-sm text-ink placeholder:text-muted";

interface FieldProps {
  name: FieldName;
  label?: string;
  hint?: string;
  value: string;
  error?: string;
  onChange: (name: FieldName, value: string) => void;
  disabled: boolean;
  type?: string;
  placeholder?: string;
  inputMode?: "decimal";
  step?: string;
}

function Field({ name, label, hint, value, error, onChange, disabled, ...rest }: FieldProps) {
  const describedBy = [hint && `${name}-hint`, error && `${name}-error`].filter(Boolean).join(" ") || undefined;
  return (
    <div>
      <label htmlFor={name} className="text-sm font-medium text-ink">{label ?? FIELD_LABELS[name]}</label>
      <input
        id={name}
        name={name}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(name, e.target.value)}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={`${base} ${error ? "border-danger" : "border-line-strong"} disabled:bg-sunken disabled:text-muted`}
        {...rest}
      />
      {hint && <p id={`${name}-hint`} className="mt-1 text-xs text-muted">{hint}</p>}
      {error && <p id={`${name}-error`} className="mt-1 text-xs font-medium text-danger">{error}</p>}
    </div>
  );
}

interface Props {
  values: FormValues;
  errors: FieldErrors;
  activeDemo: string | null;
  loading: boolean;
  onChange: (name: FieldName, value: string) => void;
  onSelectDemo: (s: DemoScenario) => void;
  onSubmit: () => void;
}

export function TransactionForm({ values, errors, activeDemo, loading, onChange, onSelectDemo, onSubmit }: Props) {
  const shared = { onChange, disabled: loading };
  const active = DEMO_SCENARIOS.find((s) => s.id === activeDemo);
  return (
    <form
      noValidate
      className="grid gap-4"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
    >
      <fieldset className="rounded-control border border-line bg-sunken/60 p-3">
        <legend className="px-1 text-sm font-medium text-ink">Demo inputs</legend>
        <p className="text-xs text-muted">Sample data for trying the screen. Not real transactions.</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {DEMO_SCENARIOS.filter((s) => USE_MOCK_API || !s.mockOnly).map((s) => (
            <button
              key={s.id}
              type="button"
              disabled={loading}
              aria-pressed={s.id === activeDemo}
              title={s.hint}
              onClick={() => onSelectDemo(s)}
              className={`min-h-11 rounded-pill border px-3 text-sm transition-colors disabled:cursor-not-allowed disabled:text-muted ${
                s.id === activeDemo ? "border-primary bg-primary-soft font-medium text-primary" : "border-line-strong bg-surface text-ink hover:bg-sunken"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
        <p className="mt-2 text-xs text-muted" aria-live="polite">
          {active ? `Loaded “${active.label}”: ${active.hint}.` : "Custom input"}
        </p>
      </fieldset>

      <Field name="transaction_amount" value={values.transaction_amount} error={errors.transaction_amount} type="number" step="any" inputMode="decimal" placeholder="128.50" {...shared} />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
        <Field name="transaction_type" hint="Required by the API. The model does not use it." value={values.transaction_type} error={errors.transaction_type} placeholder="purchase" {...shared} />
        <div>
          <label htmlFor="merchant_category" className="text-sm font-medium text-ink">{FIELD_LABELS.merchant_category}</label>
          <select
            id="merchant_category"
            name="merchant_category"
            value={values.merchant_category}
            disabled={loading}
            onChange={(e) => onChange("merchant_category", e.target.value)}
            aria-invalid={errors.merchant_category ? true : undefined}
            aria-describedby={errors.merchant_category ? "merchant_category-error" : undefined}
            className={`${base} ${errors.merchant_category ? "border-danger" : "border-line-strong"} disabled:bg-sunken disabled:text-muted`}
          >
            <option value="">Select a category</option>
            {MERCHANT_CATEGORIES.map((c) => <option key={c} value={c}>{categoryLabel(c)}</option>)}
          </select>
          {errors.merchant_category && <p id="merchant_category-error" className="mt-1 text-xs font-medium text-danger">{errors.merchant_category}</p>}
        </div>
      </div>
      <Field name="transaction_time" value={values.transaction_time} error={errors.transaction_time} type="datetime-local" {...shared} />

      <div className="grid gap-4 sm:grid-cols-2">
        <Field name="customer_latitude" label="Customer latitude" hint="Example: 23.8103" value={values.customer_latitude} error={errors.customer_latitude} type="number" step="any" inputMode="decimal" placeholder="23.8103" {...shared} />
        <Field name="customer_longitude" label="Customer longitude" hint="Example: 90.4125" value={values.customer_longitude} error={errors.customer_longitude} type="number" step="any" inputMode="decimal" placeholder="90.4125" {...shared} />
        <Field name="merchant_latitude" label="Merchant latitude" hint="Example: 22.3569" value={values.merchant_latitude} error={errors.merchant_latitude} type="number" step="any" inputMode="decimal" placeholder="22.3569" {...shared} />
        <Field name="merchant_longitude" label="Merchant longitude" hint="Example: 91.7832" value={values.merchant_longitude} error={errors.merchant_longitude} type="number" step="any" inputMode="decimal" placeholder="91.7832" {...shared} />
      </div>

      <Field name="distance_from_home" label="Distance from home (km)" hint="Optional fallback. If coordinates are provided, distance is calculated automatically." value={values.distance_from_home} error={errors.distance_from_home} type="number" step="any" inputMode="decimal" placeholder="3.2" {...shared} />

      <Button type="submit" disabled={loading} aria-busy={loading}>
        {loading && <span aria-hidden="true" className="mr-2 size-4 animate-spin rounded-full border-2 border-line-strong border-t-primary motion-reduce:animate-none" />}
        {loading ? "Analyzing…" : "Analyze transaction"}
      </Button>
    </form>
  );
}
