/// <reference types="vite/client" />

declare module 'vue-sonner' {
  import type { Component } from 'vue'
  export const Toaster: Component
  export const toast: {
    (message: string, options?: { description?: string }): void
    success: (message: string, options?: { description?: string }) => void
    error: (message: string, options?: { description?: string }) => void
    promise: <T>(promise: Promise<T>, options: { loading?: string; success?: string; error?: string }) => void
  }
}

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
