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

export const nameSchema = z.string()
  .min(1, 'Name is required')
  .max(255, 'Name cannot exceed 255 characters')

// Common form schemas
export const loginFormSchema = z.object({
  email: emailSchema,
  password: z.string().min(8, 'Password must be at least 8 characters')
    .regex(/\d/, 'Password must contain at least one number'),
})

export const signupFormSchema = z.object({
  name: nameSchema,
  email: emailSchema,
  password: passwordSchema,
  confirmPassword: z.string().min(1, 'Please confirm your password'),
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
  old_password: z.string().min(1, 'Current password is required'),
  new_password1: passwordSchema,
  new_password2: z.string().min(1, 'Please confirm your password'),
}).refine((data) => data.new_password1 === data.new_password2, {
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
