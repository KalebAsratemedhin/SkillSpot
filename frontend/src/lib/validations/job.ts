import { z } from 'zod'

export const jobCreateSchema = z
  .object({
    title: z.string().trim().min(1, 'Job title is required'),
    description: z.string().trim().min(1, 'Description is required'),
    /** Street / area text — required. */
    address: z.string().trim().min(1, 'Address is required'),
    budget_type: z.enum(['hourly', 'fixed'], {
      required_error: 'Select a payment schedule',
    }),
    rate_hourly: z.string().optional().default(''),
    price_fixed: z.string().optional().default(''),
    skill_ids: z.array(z.string()).default([]),
    /** Map pin — optional. */
    latitude: z.number().nullable().optional(),
    longitude: z.number().nullable().optional(),
  })
  .superRefine((data, ctx) => {
    if (data.budget_type === 'hourly') {
      const raw = String(data.rate_hourly ?? '').trim()
      if (!raw) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Hourly rate is required',
          path: ['rate_hourly'],
        })
        return
      }
      const n = Number(raw)
      if (!Number.isFinite(n) || n < 0) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Enter a valid hourly rate',
          path: ['rate_hourly'],
        })
      }
      return
    }

    const raw = String(data.price_fixed ?? '').trim()
    if (!raw) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Fixed price is required',
        path: ['price_fixed'],
      })
      return
    }
    const n = Number(raw)
    if (!Number.isFinite(n) || n < 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Enter a valid fixed price',
        path: ['price_fixed'],
      })
    }
  })

export type JobCreateFormData = z.infer<typeof jobCreateSchema>
