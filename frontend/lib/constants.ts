/** The 14 merchant categories the model was trained on (confirmed by Person B). */
export const MERCHANT_CATEGORIES = [
  "entertainment", "food_dining", "gas_transport", "grocery_net", "grocery_pos", "health_fitness", "home",
  "kids_pets", "misc_net", "misc_pos", "personal_care", "shopping_net", "shopping_pos", "travel",
] as const;

export function categoryLabel(value: string): string {
  const text = value.replace(/_/g, " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}
