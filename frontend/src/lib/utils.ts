import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** Platform settlement currency (Stripe Connect payouts). */
export const DEFAULT_CURRENCY = 'USD'

/** Format amount in US dollars. */
export function formatMoney(amount: number | string | undefined | null): string {
  if (amount == null || amount === '') return '$0'
  const n = typeof amount === 'string' ? parseFloat(amount) : Number(amount)
  if (Number.isNaN(n)) return '$0'
  return (
    '$' +
    n.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
  )
}

/** @deprecated Use formatMoney — kept so older imports keep working. */
export const formatETB = formatMoney
