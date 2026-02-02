import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** Format amount in Ethiopian Birr (ETB). Platform displays all money in ETB. */
export function formatETB(amount: number | string | undefined | null): string {
  if (amount == null || amount === '') return 'Br 0'
  const n = typeof amount === 'string' ? parseFloat(amount) : Number(amount)
  if (Number.isNaN(n)) return 'Br 0'
  return 'Br ' + n.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}
