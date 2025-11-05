import { createSystem, defaultConfig } from '@chakra-ui/react'

// Custom theme configuration with glassmorphism styles
const customConfig = {
  ...defaultConfig,
  theme: {
    ...defaultConfig.theme,
    colors: {
      ...defaultConfig.theme.colors,
      // Glass effect colors
      glass: {
        50: 'rgba(255, 255, 255, 0.1)',
        100: 'rgba(255, 255, 255, 0.2)',
        200: 'rgba(255, 255, 255, 0.3)',
        300: 'rgba(255, 255, 255, 0.4)',
        400: 'rgba(255, 255, 255, 0.5)',
        500: 'rgba(255, 255, 255, 0.6)',
        600: 'rgba(255, 255, 255, 0.7)',
        700: 'rgba(255, 255, 255, 0.8)',
        800: 'rgba(255, 255, 255, 0.9)',
        900: 'rgba(255, 255, 255, 0.95)',
      },
      // Dark glass effect colors
      'glass-dark': {
        50: 'rgba(0, 0, 0, 0.1)',
        100: 'rgba(0, 0, 0, 0.2)',
        200: 'rgba(0, 0, 0, 0.3)',
        300: 'rgba(0, 0, 0, 0.4)',
        400: 'rgba(0, 0, 0, 0.5)',
        500: 'rgba(0, 0, 0, 0.6)',
        600: 'rgba(0, 0, 0, 0.7)',
        700: 'rgba(0, 0, 0, 0.8)',
        800: 'rgba(0, 0, 0, 0.9)',
        900: 'rgba(0, 0, 0, 0.95)',
      },
      // Gradient colors - subtle white-based
      gradient: {
        primary: 'linear-gradient(135deg, #3b82f6 0%, #6366f1 100%)',
        success: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
        error: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
        background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
        'background-dark': 'linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%)',
      }
    },
    components: {
      ...defaultConfig.theme.components,
      Box: {
        baseStyle: {
          _light: {
            '&.glass': {
              backdropFilter: 'blur(10px)',
              background: 'rgba(255, 255, 255, 0.7)',
              border: '1px solid rgba(255, 255, 255, 0.8)',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.05)',
            },
            '&.glass-strong': {
              backdropFilter: 'blur(20px)',
              background: 'rgba(255, 255, 255, 0.8)',
              border: '1px solid rgba(255, 255, 255, 0.9)',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.08)',
            }
          },
          _dark: {
            '&.glass': {
              backdropFilter: 'blur(10px)',
              background: 'rgba(0, 0, 0, 0.2)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
            },
            '&.glass-strong': {
              backdropFilter: 'blur(20px)',
              background: 'rgba(0, 0, 0, 0.3)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
            }
          }
        }
      },
      Button: {
        baseStyle: {
          borderRadius: '12px',
          fontWeight: '500',
          transition: 'all 0.2s ease-in-out',
          _hover: {
            transform: 'translateY(-2px)',
            boxShadow: '0 8px 25px rgba(0, 0, 0, 0.15)',
          },
          _active: {
            transform: 'translateY(0)',
          }
        },
        variants: {
          glass: {
            backdropFilter: 'blur(10px)',
            background: 'rgba(255, 255, 255, 0.1)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            color: 'white',
            _hover: {
              background: 'rgba(255, 255, 255, 0.2)',
              transform: 'translateY(-2px)',
            }
          },
          gradient: {
            background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
            color: 'white',
            border: 'none',
            _hover: {
              background: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
              transform: 'translateY(-2px)',
            }
          }
        }
      },
      Card: {
        baseStyle: {
          borderRadius: '16px',
          backdropFilter: 'blur(10px)',
          background: 'rgba(255, 255, 255, 0.1)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          transition: 'all 0.3s ease-in-out',
          _hover: {
            transform: 'translateY(-4px)',
            boxShadow: '0 12px 40px rgba(0, 0, 0, 0.15)',
          }
        }
      },
      Input: {
        baseStyle: {
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          background: 'rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(10px)',
          _focus: {
            borderColor: '#3b82f6',
            boxShadow: '0 0 0 3px rgba(59, 130, 246, 0.1)',
          },
          _placeholder: {
            color: 'rgba(255, 255, 255, 0.6)',
          }
        }
      },
      Textarea: {
        baseStyle: {
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          background: 'rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(10px)',
          _focus: {
            borderColor: '#3b82f6',
            boxShadow: '0 0 0 3px rgba(59, 130, 246, 0.1)',
          },
          _placeholder: {
            color: 'rgba(255, 255, 255, 0.6)',
          }
        }
      }
    },
    styles: {
        global: {
          body: {
            background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
            minHeight: '100vh',
            fontFamily: 'Inter, system-ui, sans-serif',
          },
          'body.dark': {
            background: 'linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%)',
          },
        '*': {
          scrollbarWidth: 'thin',
          scrollbarColor: 'rgba(255, 255, 255, 0.3) transparent',
        },
        '::-webkit-scrollbar': {
          width: '8px',
        },
        '::-webkit-scrollbar-track': {
          background: 'transparent',
        },
        '::-webkit-scrollbar-thumb': {
          background: 'rgba(255, 255, 255, 0.3)',
          borderRadius: '4px',
        },
        '::-webkit-scrollbar-thumb:hover': {
          background: 'rgba(255, 255, 255, 0.5)',
        }
      }
    }
  }
}

export const system = createSystem(customConfig)
