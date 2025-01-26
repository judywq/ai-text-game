import { z } from 'zod'

// Basic validations
export const emailSchema = z.string()
  .min(1, 'Email is required')
  .email('Invalid email address')

export const passwordSchema = z.string()
  .min(8, 'Password must be at least 8 characters')
  .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
  .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
  .regex(/\d/, 'Password must contain at least one number')

// Common form schemas
export const loginFormSchema = z.object({
  email: emailSchema,
  password: z.string().min(8, 'Password must be at least 8 characters')
    .regex(/\d/, 'Password must contain at least one number'),
})

export const signupFormSchema = z.object({
  email: emailSchema,
  password: passwordSchema,
  confirmPassword: z.string().min(1, 'Please confirm your password'),
  course_id: z.union([
    z.string().transform((val) => {
      // Convert empty string to undefined
      if (val === '') return undefined;
      // Convert string to number
      const num = parseInt(val, 10);
      // Return undefined if NaN, otherwise return the number
      return isNaN(num) ? undefined : num;
    }),
    z.number(),
  ]).optional(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
})

export const resetPasswordFormSchema = z.object({
  password: passwordSchema,
  confirmPassword: z.string().min(1, 'Please confirm your password'),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
})

export const changePasswordFormSchema = z.object({
  currentPassword: z.string().min(1, 'Current password is required'),
  newPassword: passwordSchema,
  confirmPassword: z.string().min(1, 'Please confirm your password'),
}).refine((data) => data.newPassword === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
})

export const forgotPasswordFormSchema = z.object({
  email: emailSchema,
})

export const verifyEmailFormSchema = z.object({
  verificationCode: z.string().min(1, 'Verification code is required'),
})

export const MAX_CHARS = 5000

// Add validation schema
export const essayFormSchema = z.object({
  essay: z.string()
    .min(1, 'Please enter your essay')
    .max(MAX_CHARS, `Text cannot exceed ${MAX_CHARS} characters`),
  model_name: z.string().min(1, 'Please select a model'),
})
