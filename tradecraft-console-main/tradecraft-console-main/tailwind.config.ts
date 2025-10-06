import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./pages/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./app/**/*.{ts,tsx}", "./src/**/*.{ts,tsx}"],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        
        /* Trading Platform Colors */
        panel: "hsl(var(--panel))",
        "panel-alt": "hsl(var(--panel-alt))",
        
        /* Trading Semantic Colors */
        "trading-success": "hsl(var(--trading-success))",
        "trading-success-bg": "hsl(var(--trading-success-bg))",
        "trading-danger": "hsl(var(--trading-danger))",
        "trading-danger-bg": "hsl(var(--trading-danger-bg))",
        "trading-warning": "hsl(var(--trading-warning))",
        "trading-warning-bg": "hsl(var(--trading-warning-bg))",
        "trading-info": "hsl(var(--trading-info))",
        "trading-info-bg": "hsl(var(--trading-info-bg))",
        
        /* Base System Colors */
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
          hover: "hsl(var(--primary-hover))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
          hover: "hsl(var(--secondary-hover))",
        },
        
        /* Text Hierarchy */
        "text-primary": "hsl(var(--text-primary))",
        "text-secondary": "hsl(var(--text-secondary))",
        "text-muted": "hsl(var(--text-muted))",
        "text-disabled": "hsl(var(--text-disabled))",
        
        /* Interactive States */
        "border-hover": "hsl(var(--border-hover))",
        "input-border": "hsl(var(--input-border))",
        
        /* Status Colors */
        "status-online": "hsl(var(--status-online))",
        "status-offline": "hsl(var(--status-offline))",
        "status-pending": "hsl(var(--status-pending))",
        
        /* Sidebar */
        sidebar: {
          DEFAULT: "hsl(var(--sidebar-background))",
          border: "hsl(var(--sidebar-border))",
          "item-hover": "hsl(var(--sidebar-item-hover))",
          "item-active": "hsl(var(--sidebar-item-active))",
        },
        
        /* Tables */
        "table-header": "hsl(var(--table-header))",
        "table-row-hover": "hsl(var(--table-row-hover))",
        "table-row-even": "hsl(var(--table-row-even))",
        
        /* Legacy Compatibility */
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius-lg)",
        md: "var(--radius-md)",
        sm: "var(--radius-sm)",
      },
      
      /* Trading Platform Spacing */
      spacing: {
        'header': 'var(--header-height)',
        'sidebar': 'var(--sidebar-width)',
        'sidebar-collapsed': 'var(--sidebar-collapsed)',
        'panel-gap': 'var(--panel-gap)',
      },
      
      /* Typography */
      fontFamily: {
        mono: ['var(--font-mono)'],
      },
      
      /* Shadows */
      boxShadow: {
        'trading-sm': 'var(--shadow-sm)',
        'trading-md': 'var(--shadow-md)',
        'trading-lg': 'var(--shadow-lg)',
      },
      
      /* Transitions */
      transitionDuration: {
        'fast': 'var(--transition-fast)',
        'normal': 'var(--transition-normal)',
      },
      keyframes: {
        "accordion-down": {
          from: {
            height: "0",
          },
          to: {
            height: "var(--radix-accordion-content-height)",
          },
        },
        "accordion-up": {
          from: {
            height: "var(--radix-accordion-content-height)",
          },
          to: {
            height: "0",
          },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config;
